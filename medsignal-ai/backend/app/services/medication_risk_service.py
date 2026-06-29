from dataclasses import dataclass

from app.models.medication_list import MedicationList, MedicationRiskProfile
from app.services.interaction_service import DRUG_CLASS_CATEGORIES


RISK_PROFILE_DISCLAIMER = (
    "This questionnaire is for education and appointment preparation. It does "
    "not diagnose, score risk, or provide medical advice. Discuss these factors "
    "with a clinician or pharmacist, and do not stop prescribed medication "
    "without medical advice."
)


@dataclass(frozen=True)
class RiskFactorDefinition:
    key: str
    label: str
    help_text: str
    input_type: str = "checkbox"


RISK_FACTOR_DEFINITIONS = (
    RiskFactorDefinition(
        "alcohol_use",
        "Alcohol use",
        "Alcohol may increase concern with sedating medicines or other label warnings.",
    ),
    RiskFactorDefinition(
        "smoking",
        "Smoking",
        "Smoking can be relevant to medication metabolism and some safety warnings.",
    ),
    RiskFactorDefinition(
        "liver_disease",
        "Liver disease",
        "Liver conditions may increase concern for medicines with metabolism or label-warning considerations.",
    ),
    RiskFactorDefinition(
        "kidney_disease",
        "Kidney disease",
        "Kidney conditions may increase concern with medicines that can affect kidney function.",
    ),
    RiskFactorDefinition(
        "pregnancy_breastfeeding",
        "Pregnancy or breastfeeding",
        "Pregnancy or breastfeeding can change medication risk-benefit discussions.",
    ),
    RiskFactorDefinition(
        "blood_thinner_use",
        "Blood thinner use",
        "Blood thinners may increase concern with medicines that affect bleeding risk.",
    ),
    RiskFactorDefinition(
        "diabetes_medication_use",
        "Diabetes medication use",
        "Diabetes medicines can be relevant to medication review and monitoring conversations.",
    ),
    RiskFactorDefinition(
        "blood_pressure_medication_use",
        "Blood pressure medication use",
        "Blood pressure medicines can be relevant to dizziness, falls, or blood-pressure-effect discussions.",
    ),
    RiskFactorDefinition(
        "allergies",
        "Allergies",
        "List medication or ingredient allergies to review before taking new medicines.",
        "text",
    ),
    RiskFactorDefinition(
        "age_65_plus",
        "Age 65+",
        "Age 65+ may increase concern for side effects, falls, or dose sensitivity.",
    ),
    RiskFactorDefinition(
        "stomach_bleeding_ulcers",
        "History of stomach bleeding or ulcers",
        "Prior bleeding or ulcers may increase concern with NSAIDs or blood thinners.",
    ),
    RiskFactorDefinition(
        "breathing_sleep_apnea",
        "History of breathing problems or sleep apnea",
        "Breathing problems or sleep apnea may increase concern with sedating medicines.",
    ),
)
RISK_FACTOR_BY_KEY = {factor.key: factor for factor in RISK_FACTOR_DEFINITIONS}


def serialize_risk_profile(profile: MedicationRiskProfile) -> dict:
    factor_by_key = {factor.factor_key: factor for factor in profile.factors}
    return {
        "id": profile.id,
        "medication_list_id": profile.medication_list_id,
        "factors": [
            {
                "factor_key": definition.key,
                "label": definition.label,
                "help_text": definition.help_text,
                "input_type": definition.input_type,
                "is_present": factor_by_key.get(definition.key).is_present
                if definition.key in factor_by_key
                else False,
                "note": factor_by_key.get(definition.key).note
                if definition.key in factor_by_key
                else None,
            }
            for definition in RISK_FACTOR_DEFINITIONS
        ],
        "factors_to_discuss": risk_factors_to_discuss(profile),
        "disclaimer": RISK_PROFILE_DISCLAIMER,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }


def risk_factors_to_discuss(profile: MedicationRiskProfile) -> list[dict]:
    selected = {
        factor.factor_key: factor
        for factor in profile.factors
        if factor.is_present or (factor.note and factor.note.strip())
    }
    medication_matches = _medication_matches(profile.medication_list)
    discussion_items: list[dict] = []

    for key, factor in selected.items():
        definition = RISK_FACTOR_BY_KEY.get(key)
        if definition is None:
            continue
        connected_categories, matched_medications, concern = _discussion_context(
            key,
            medication_matches,
            bool(factor.note and factor.note.strip()),
        )
        discussion_items.append(
            {
                "factor_key": key,
                "label": definition.label,
                "concern": concern,
                "connected_categories": connected_categories,
                "matched_medications": matched_medications,
            }
        )

    return discussion_items


def _discussion_context(
    factor_key: str,
    medication_matches: dict[str, list[str]],
    has_note: bool,
) -> tuple[list[str], list[str], str]:
    if factor_key == "alcohol_use":
        medications = _medications_for_categories(
            medication_matches, ["opioid", "benzodiazepine"]
        )
        if medications:
            return (
                ["cns_respiratory_depression"],
                medications,
                "Alcohol use may increase concern with CNS depressant medications; discuss this combination with a clinician or pharmacist.",
            )
        return (
            ["label_warning_concern"],
            [],
            "Alcohol use may be relevant to medication label warnings; discuss this with a clinician or pharmacist.",
        )

    if factor_key == "stomach_bleeding_ulcers":
        medications = _medications_for_categories(
            medication_matches, ["nsaid", "anticoagulant", "antiplatelet"]
        )
        categories = ["bleeding"] if medications else ["medical_history"]
        return (
            categories,
            medications,
            "A history of stomach bleeding or ulcers may increase concern with NSAID or anticoagulant bleeding risk; discuss this with a clinician or pharmacist.",
        )

    if factor_key == "kidney_disease":
        medications = _medications_for_categories(medication_matches, ["nsaid"])
        return (
            ["renal_label_warning"],
            medications,
            "Kidney disease may increase concern with NSAID-related kidney risk or other medication label warnings; discuss this with a clinician or pharmacist.",
        )

    if factor_key == "liver_disease":
        return (
            ["metabolism", "label_warning_concern"],
            [],
            "Liver disease may increase concern for metabolism or label-warning issues; discuss this with a clinician or pharmacist.",
        )

    if factor_key == "breathing_sleep_apnea":
        medications = _medications_for_categories(
            medication_matches, ["opioid", "benzodiazepine"]
        )
        return (
            ["cns_respiratory_depression"],
            medications,
            "Breathing problems or sleep apnea may increase concern with opioid or benzodiazepine CNS/respiratory effects; discuss this with a clinician or pharmacist.",
        )

    if factor_key == "blood_thinner_use":
        medications = _medications_for_categories(
            medication_matches, ["nsaid", "anticoagulant", "antiplatelet"]
        )
        return (
            ["bleeding"],
            medications,
            "Blood thinner use may increase concern with other bleeding-risk medicines; discuss this with a clinician or pharmacist.",
        )

    if factor_key == "allergies" and has_note:
        return (
            ["allergy_review"],
            [],
            "Medication or ingredient allergies should be reviewed with a clinician or pharmacist before starting new medicines.",
        )

    return (
        ["patient_context"],
        [],
        f"{RISK_FACTOR_BY_KEY[factor_key].label} may be relevant to medication review; discuss this with a clinician or pharmacist.",
    )


def _medication_matches(medication_list: MedicationList) -> dict[str, list[str]]:
    matches: dict[str, set[str]] = {
        category: set() for category in DRUG_CLASS_CATEGORIES.keys()
    }
    for item in medication_list.items:
        drug = item.drug
        haystack = " ".join(
            value
            for value in [
                drug.input_name,
                drug.normalized_name,
                drug.synonym,
                drug.rxcui,
            ]
            if value
        ).casefold()
        display_name = drug.normalized_name or drug.input_name
        for category, terms in DRUG_CLASS_CATEGORIES.items():
            if any(term in haystack for term in terms):
                matches[category].add(display_name)
    return {key: sorted(value) for key, value in matches.items()}


def _medications_for_categories(
    medication_matches: dict[str, list[str]],
    categories: list[str],
) -> list[str]:
    medications: set[str] = set()
    for category in categories:
        medications.update(medication_matches.get(category, []))
    return sorted(medications)
