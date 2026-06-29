from app.models.drug import Drug
from app.models.medication_list import (
    MedicationList,
    MedicationListItem,
    MedicationRiskFactor,
    MedicationRiskProfile,
)
from app.services.medication_risk_service import risk_factors_to_discuss


def make_profile(factors: list[MedicationRiskFactor]) -> MedicationRiskProfile:
    medication_list = MedicationList(id=1, name="My medications")
    medication_list.items = [
        MedicationListItem(
            id=1,
            drug=Drug(
                id=1,
                rxcui="5640",
                input_name="ibuprofen",
                normalized_name="ibuprofen",
                synonym="nonsteroidal anti-inflammatory",
                tty="IN",
            ),
        ),
        MedicationListItem(
            id=2,
            drug=Drug(
                id=2,
                rxcui="11289",
                input_name="warfarin",
                normalized_name="warfarin",
                synonym="vitamin k antagonist",
                tty="IN",
            ),
        ),
        MedicationListItem(
            id=3,
            drug=Drug(
                id=3,
                rxcui="5489",
                input_name="hydrocodone",
                normalized_name="hydrocodone",
                synonym="opioid analgesic",
                tty="IN",
            ),
        ),
    ]
    profile = MedicationRiskProfile(
        id=1,
        medication_list_id=medication_list.id,
        medication_list=medication_list,
    )
    profile.factors = factors
    return profile


def test_risk_factor_summary_connects_history_to_medication_categories():
    profile = make_profile(
        [
            MedicationRiskFactor(
                factor_key="stomach_bleeding_ulcers",
                is_present=True,
            ),
            MedicationRiskFactor(
                factor_key="breathing_sleep_apnea",
                is_present=True,
            ),
        ]
    )

    summary = risk_factors_to_discuss(profile)

    bleeding_item = next(
        item for item in summary if item["factor_key"] == "stomach_bleeding_ulcers"
    )
    breathing_item = next(
        item for item in summary if item["factor_key"] == "breathing_sleep_apnea"
    )
    assert bleeding_item["connected_categories"] == ["bleeding"]
    assert bleeding_item["matched_medications"] == ["ibuprofen", "warfarin"]
    assert "may increase concern" in bleeding_item["concern"]
    assert breathing_item["connected_categories"] == ["cns_respiratory_depression"]
    assert breathing_item["matched_medications"] == ["hydrocodone"]
    assert "discuss" in breathing_item["concern"]


def test_risk_factor_summary_uses_notes_without_diagnosing():
    profile = make_profile(
        [
            MedicationRiskFactor(
                factor_key="allergies",
                is_present=False,
                note="Penicillin",
            )
        ]
    )

    summary = risk_factors_to_discuss(profile)

    assert summary == [
        {
            "factor_key": "allergies",
            "label": "Allergies",
            "concern": (
                "Medication or ingredient allergies should be reviewed with a "
                "clinician or pharmacist before starting new medicines."
            ),
            "connected_categories": ["allergy_review"],
            "matched_medications": [],
        }
    ]
