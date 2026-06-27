import re
from typing import Any

import httpx

from app.core.config import get_settings
from app.models.medication_list import MedicationList


class InteractionUpstreamError(Exception):
    pass


class InteractionTimeoutError(Exception):
    pass


INTERACTION_DISCLAIMER = (
    "This screening uses RxNorm identifiers to retrieve openFDA label "
    "drug_interactions text for education and appointment preparation. Label "
    "text can be incomplete, may not mention every clinically relevant "
    "combination, and does not replace review by a doctor or pharmacist."
)

OPENFDA_LABEL_SOURCE = "openFDA drug label"
LABEL_INTERACTION_FIELD = "drug_interactions"
LABEL_SECTION_FIELDS = (
    "boxed_warning",
    "warnings",
    "warnings_and_precautions",
    "contraindications",
    "drug_interactions",
)
EXCERPT_LENGTH = 650
RXCLASS_ALLOWED_CLASS_TYPES = {"ATC1-4", "EPC", "VA"}
PK_TERMS = {
    "cyp",
    "cyp2c9",
    "cyp2d6",
    "cyp3a",
    "cyp3a4",
    "enzyme",
    "inducer",
    "induction",
    "inhibitor",
    "inhibition",
    "substrate",
}
PD_TERMS = {
    "bleeding",
    "cns depressant",
    "coma",
    "death",
    "gastrointestinal",
    "hemorrhage",
    "hypotension",
    "mucosa",
    "platelet",
    "profound sedation",
    "respiratory depression",
    "sedation",
}
RISK_TERMS = {
    "bleeding",
    "coma",
    "death",
    "hypotension",
    "overdose",
    "profound sedation",
    "respiratory depression",
    "sedation",
    "serotonin syndrome",
    "toxicity",
}
RISK_CATEGORY_TERMS = {
    "bleeding": {"bleeding", "hemorrhage", "haemorrhage"},
    "cns_respiratory_depression": {
        "cns depressant",
        "coma",
        "profound sedation",
        "respiratory depression",
        "sedation",
    },
    "cyp_exposure_change": PK_TERMS,
    "hypotension": {"hypotension"},
    "serotonergic_toxicity": {"serotonin syndrome"},
}
RISK_PRIORITY_TERMS = (
    "death",
    "coma",
    "respiratory depression",
    "profound sedation",
    "hypotension",
    "bleeding",
    "toxicity",
    "sedation",
)
DRUG_CLASS_CATEGORIES = {
    "nsaid": {
        "anti-inflammatory",
        "ibuprofen",
        "nsaid",
        "nsaids",
        "nonsteroidal",
        "nonsteroidal anti-inflammatory agents",
    },
    "anticoagulant": {
        "anticoagulant",
        "anticoagulants",
        "antithrombotic",
        "vitamin k antagonist",
        "warfarin",
    },
    "antiplatelet": {
        "antiplatelet",
        "platelet aggregation inhibitors",
        "platelet inhibitor",
    },
    "opioid": {
        "opioid",
        "opioids",
        "opiate",
        "opium",
        "narcotic",
        "hydrocodone",
        "oxycodone",
    },
    "benzodiazepine": {
        "alprazolam",
        "benzodiazepine",
        "benzodiazepines",
    },
}
CLASS_TERM_STOPWORDS = {
    "administration",
    "agents",
    "and",
    "class",
    "classes",
    "combination",
    "combinations",
    "derivatives",
    "dosage",
    "drugs",
    "drug",
    "enzymes",
    "ii",
    "iii",
    "information",
    "inducers",
    "inhibitors",
    "iv",
    "medication",
    "medications",
    "patient",
    "patients",
    "prescribing",
    "substrates",
    "non",
    "other",
    "products",
    "schedule",
    "with",
}


def screen_medication_list_interactions(medication_list: MedicationList) -> dict[str, Any]:
    medication_items = _interaction_items(medication_list)
    rxcuis = [item["rxcui"] for item in medication_items if item["rxcui"]]
    unique_rxcuis = sorted(set(rxcuis))
    if len(unique_rxcuis) < 2:
        return {
            "medication_list_id": medication_list.id,
            "checked_rxcuis": unique_rxcuis,
            "interactions": [],
            "disclaimer": INTERACTION_DISCLAIMER,
        }

    _enrich_with_rxclass_terms(medication_items)
    return {
        "medication_list_id": medication_list.id,
        "checked_rxcuis": unique_rxcuis,
        "interactions": _openfda_label_interactions(medication_items),
        "disclaimer": INTERACTION_DISCLAIMER,
    }


def _openfda_label_interactions(
    medication_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    interactions_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    seen_evidence: set[tuple[Any, ...]] = set()

    for source_item in medication_items:
        labels = _query_openfda_labels(source_item)
        for label in labels:
            sections = _label_sections(label)
            if not sections:
                continue

            found_pair_for_label = False
            for target_item in medication_items:
                if target_item["rxcui"] == source_item["rxcui"]:
                    continue

                match = _hierarchy_pd_match(source_item, target_item, sections)
                if match is None:
                    match = _matching_excerpt(sections, target_item["terms"])
                if match is None:
                    continue
                excerpt, matched_term, label_section = match

                evidence_key = (
                    "pair",
                    source_item["rxcui"],
                    target_item["rxcui"],
                    label_section,
                    excerpt.casefold(),
                )
                if evidence_key in seen_evidence:
                    continue
                seen_evidence.add(evidence_key)
                found_pair_for_label = True
                _add_pair_interaction(
                    interactions_by_key,
                    source_item,
                    target_item,
                    matched_term,
                    label_section,
                    excerpt,
                )

            if found_pair_for_label:
                continue

            interaction_sections = [
                section
                for section in sections
                if section["label_section"] == LABEL_INTERACTION_FIELD
            ]
            excerpt = _first_excerpt(interaction_sections or sections)
            evidence_key = ("label", source_item["rxcui"], excerpt.casefold())
            if evidence_key in seen_evidence:
                continue
            seen_evidence.add(evidence_key)
            _add_label_guidance_interaction(interactions_by_key, source_item, excerpt)

    return list(interactions_by_key.values())


def _add_pair_interaction(
    interactions_by_key: dict[tuple[Any, ...], dict[str, Any]],
    source_item: dict[str, Any],
    target_item: dict[str, Any],
    matched_term: str,
    label_section: str,
    excerpt: str,
) -> None:
    key = ("pair", *sorted([source_item["rxcui"], target_item["rxcui"]]))
    drugs = sorted(
        [
            {"rxcui": source_item["rxcui"], "name": source_item["name"]},
            {"rxcui": target_item["rxcui"], "name": target_item["name"]},
        ],
        key=lambda drug: drug["name"].casefold(),
    )
    interaction = interactions_by_key.setdefault(
        key,
        {
            "source": OPENFDA_LABEL_SOURCE,
            "severity": "FDA label-backed guidance",
            "severity_tier": "tier_2_major_monitor",
            "mechanism": "unknown",
            "risk_category": "label_interaction_guidance",
            "description": (
                "FDA label drug interaction guidance was found for "
                f"{drugs[0]['name']} + {drugs[1]['name']}."
            ),
            "explanation": (
                "MedSignal matched FDA label text to the other medication's "
                "RxNorm name or RxClass terminology. Review the source excerpts "
                "with a clinician or pharmacist."
            ),
            "assessment_reason": (
                "Initial label-backed match. Mechanism and tier are refined as "
                "FDA evidence is added."
            ),
            "drugs": drugs,
            "evidence": [],
        },
    )
    interaction["evidence"].append(
        _evidence(
            source_item=source_item,
            target_item=target_item,
            matched_term=matched_term,
            label_section=label_section,
            excerpt=excerpt,
        )
    )
    _apply_interaction_assessment(interaction, [source_item, target_item])


def _add_label_guidance_interaction(
    interactions_by_key: dict[tuple[Any, ...], dict[str, Any]],
    source_item: dict[str, Any],
    excerpt: str,
) -> None:
    key = ("label", source_item["rxcui"])
    interactions_by_key[key] = {
        "source": OPENFDA_LABEL_SOURCE,
        "severity": "FDA label guidance",
        "severity_tier": "tier_3_moderate_adjust",
        "mechanism": "unknown",
        "risk_category": "label_interaction_guidance",
        "description": (
            f"{source_item['name']} has drug interaction guidance in its FDA "
            "label, but the text did not explicitly name another medication "
            "in this cabinet."
        ),
        "explanation": (
            "This is general FDA label interaction guidance for one medication, "
            "not a confirmed pair-specific match."
        ),
        "assessment_reason": (
            "General label interaction guidance without a pair-specific class "
            "or medication match."
        ),
        "drugs": [{"rxcui": source_item["rxcui"], "name": source_item["name"]}],
        "evidence": [
            _evidence(
                source_item=source_item,
                target_item=None,
                matched_term=None,
                label_section=LABEL_INTERACTION_FIELD,
                excerpt=excerpt,
            )
        ],
    }


def _evidence(
    source_item: dict[str, Any],
    target_item: dict[str, Any] | None,
    matched_term: str | None,
    label_section: str,
    excerpt: str,
) -> dict[str, Any]:
    return {
        "source_drug_name": source_item["name"],
        "source_rxcui": source_item["rxcui"],
        "matched_drug_name": target_item["name"] if target_item else None,
        "matched_rxcui": target_item["rxcui"] if target_item else None,
        "matched_term": matched_term,
        "match_type": _match_type(target_item, matched_term),
        "label_section": label_section,
        "risk_statement": _risk_statement(excerpt),
        "excerpt": excerpt,
    }


def _match_type(target_item: dict[str, Any] | None, matched_term: str | None) -> str:
    if target_item is None or matched_term is None:
        return "general label guidance"
    return target_item["term_sources"].get(matched_term, "RxClass class match")


def _apply_interaction_assessment(
    interaction: dict[str, Any], items: list[dict[str, Any]]
) -> None:
    evidence_text = " ".join(
        " ".join(
            str(evidence.get(field) or "")
            for field in ("matched_term", "risk_statement", "excerpt")
        )
        for evidence in interaction["evidence"]
    ).casefold()
    categories = {category for item in items for category in item["categories"]}

    hierarchy = _hierarchy_assessment(categories)
    if hierarchy is not None:
        interaction.update(hierarchy)
        return

    has_pk = any(term in evidence_text for term in PK_TERMS)
    has_pd = any(term in evidence_text for term in PD_TERMS)
    mechanism = (
        "mixed"
        if has_pk and has_pd
        else "pharmacokinetic"
        if has_pk
        else "pharmacodynamic"
        if has_pd
        else "unknown"
    )
    risk_category = _risk_category(evidence_text, mechanism)
    severity_tier = _severity_tier(evidence_text, mechanism)
    interaction.update(
        {
            "severity": _severity_label(severity_tier),
            "severity_tier": severity_tier,
            "mechanism": mechanism,
            "risk_category": risk_category,
            "assessment_reason": _assessment_reason(
                mechanism, risk_category, severity_tier
            ),
        }
    )


def _hierarchy_assessment(categories: set[str]) -> dict[str, str] | None:
    if {"nsaid", "anticoagulant"}.issubset(categories):
        return {
            "severity": "Tier 1: Critical pharmacodynamic risk",
            "severity_tier": "tier_1_contraindicated_critical",
            "mechanism": "pharmacodynamic",
            "risk_category": "severe_gastrointestinal_hemorrhage",
            "assessment_reason": (
                "Hierarchy override: NSAID antiplatelet/GI mucosa effects plus "
                "anticoagulation create a critical bleeding-risk pattern. "
                "Pharmacodynamic risk takes priority over CYP table matches."
            ),
        }
    if {"opioid", "benzodiazepine"}.issubset(categories):
        return {
            "severity": "Tier 1: Critical pharmacodynamic risk",
            "severity_tier": "tier_1_contraindicated_critical",
            "mechanism": "pharmacodynamic",
            "risk_category": "cns_respiratory_depression",
            "assessment_reason": (
                "Hierarchy override: opioid plus benzodiazepine creates "
                "overlapping CNS and respiratory-depression risk."
            ),
        }
    if {"antiplatelet", "anticoagulant"}.issubset(categories):
        return {
            "severity": "Tier 1: Critical pharmacodynamic risk",
            "severity_tier": "tier_1_contraindicated_critical",
            "mechanism": "pharmacodynamic",
            "risk_category": "bleeding",
            "assessment_reason": (
                "Hierarchy override: antiplatelet effect plus anticoagulation "
                "creates an additive bleeding-risk pattern."
            ),
        }
    return None


def _risk_category(evidence_text: str, mechanism: str) -> str:
    for category, terms in RISK_CATEGORY_TERMS.items():
        if any(term in evidence_text for term in terms):
            return category
    if mechanism == "pharmacokinetic":
        return "cyp_exposure_change"
    return "label_interaction_guidance"


def _severity_tier(evidence_text: str, mechanism: str) -> str:
    if any(
        term in evidence_text
        for term in (
            "contraindicated",
            "coma",
            "death",
            "life-threatening",
            "profound sedation",
            "respiratory depression",
            "severe bleeding",
        )
    ):
        return "tier_1_contraindicated_critical"
    if any(
        term in evidence_text
        for term in ("avoid", "bleeding", "dose reduction", "monitor", "use caution")
    ):
        return "tier_2_major_monitor"
    if mechanism == "pharmacokinetic":
        return "tier_3_moderate_adjust"
    return "tier_2_major_monitor"


def _severity_label(severity_tier: str) -> str:
    return {
        "tier_1_contraindicated_critical": "Tier 1: Contraindicated/Critical",
        "tier_2_major_monitor": "Tier 2: Major/Monitor",
        "tier_3_moderate_adjust": "Tier 3: Moderate/Adjust",
    }[severity_tier]


def _assessment_reason(
    mechanism: str, risk_category: str, severity_tier: str
) -> str:
    return (
        f"Classified as {mechanism} with {risk_category} risk using FDA label "
        f"evidence and assigned {severity_tier.replace('_', ' ')}."
    )


def _query_openfda_labels(source_item: dict[str, Any]) -> list[dict[str, Any]]:
    labels: list[dict[str, Any]] = []
    rxcui = source_item["rxcui"]
    if rxcui:
        labels = _query_openfda_label_search(f'openfda.rxcui:"{_escape_phrase(rxcui)}"')
    if not labels:
        labels = _query_openfda_label_search(
            f'openfda.generic_name:"{_escape_phrase(source_item["name"])}"'
        )
    if not labels:
        labels = _query_openfda_label_search(
            f'openfda.brand_name:"{_escape_phrase(source_item["name"])}"'
        )
    return labels[:1]


def _enrich_with_rxclass_terms(medication_items: list[dict[str, Any]]) -> None:
    for item in medication_items:
        if not item["rxcui"]:
            continue
        rxclass_terms = _query_rxclass_terms(item["rxcui"])
        item["terms"].update(rxclass_terms)
        item["term_sources"].update(
            {term: "RxClass class match" for term in rxclass_terms}
        )
        item["categories"] = _class_categories(item["terms"])


def _query_rxclass_terms(rxcui: str) -> set[str]:
    settings = get_settings()
    try:
        with httpx.Client(timeout=settings.rxnorm_timeout_seconds) as client:
            response = client.get(
                f"{settings.rxnorm_base_url}/REST/rxclass/class/byRxcui.json",
                params={"rxcui": rxcui},
            )
            if response.status_code == 404:
                return set()
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError):
        return set()

    terms: set[str] = set()
    drug_info = data.get("rxclassDrugInfoList", {}).get("rxclassDrugInfo") or []
    for entry in drug_info:
        class_item = entry.get("rxclassMinConceptItem") or {}
        if class_item.get("classType") not in RXCLASS_ALLOWED_CLASS_TYPES:
            continue
        class_name = _normalize_term(class_item.get("className"))
        if not class_name:
            continue
        terms.update(_class_name_terms(class_name))
    return terms


def _query_openfda_label_search(search: str) -> list[dict[str, Any]]:
    settings = get_settings()
    try:
        with httpx.Client(timeout=settings.openfda_timeout_seconds) as client:
            response = client.get(
                f"{settings.openfda_base_url}/drug/label.json",
                params={"search": search, "limit": "1"},
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException as exc:
        raise InteractionTimeoutError("openFDA label request timed out") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise InteractionUpstreamError("openFDA label request failed") from exc

    return data.get("results", [])


def _interaction_items(medication_list: MedicationList) -> list[dict[str, Any]]:
    interaction_items: list[dict[str, Any]] = []
    for item in medication_list.items:
        if not item.drug:
            continue
        direct_terms = {
            term
            for term in (
                _normalize_term(item.drug.input_name),
                _normalize_term(item.drug.normalized_name),
                _normalize_term(item.drug.synonym),
            )
            if len(term) >= 4
        }
        interaction_items.append(
            {
                "rxcui": _clean_string(item.drug.rxcui) or "",
                "name": _clean_string(item.drug.normalized_name)
                or _clean_string(item.drug.input_name)
                or "Medication",
                "terms": set(direct_terms),
                "term_sources": {
                    term: "exact medication-name match" for term in direct_terms
                },
                "categories": _class_categories(direct_terms),
            }
        )
    return interaction_items


def _matching_excerpt(
    sections: list[dict[str, str]], target_terms: set[str]
) -> tuple[str, str, str] | None:
    for section in sections:
        normalized = _normalize_whitespace(section["text"])
        normalized_casefolded = normalized.casefold()
        matched_terms = [
            term for term in target_terms if _contains_term(normalized_casefolded, term)
        ]
        if matched_terms:
            matched_term = min(
                matched_terms,
                key=lambda term: _first_term_index(normalized_casefolded, term),
            )
            return (
                _excerpt_around_match(normalized, matched_term),
                matched_term,
                section["label_section"],
            )
    return None


def _excerpt_around_match(text: str, target_term: str) -> str:
    text_casefolded = text.casefold()
    match_index = text_casefolded.find(target_term)
    if match_index < 0:
        return _first_excerpt([{"label_section": LABEL_INTERACTION_FIELD, "text": text}])

    start = max(0, match_index - 180)
    end = min(len(text), start + EXCERPT_LENGTH)
    excerpt = text[start:end].strip()
    if start > 0:
        excerpt = f"...{excerpt}"
    if end < len(text):
        excerpt = f"{excerpt}..."
    return excerpt


def _first_excerpt(sections: list[dict[str, str]]) -> str:
    text = _normalize_whitespace(" ".join(section["text"] for section in sections))
    if len(text) <= EXCERPT_LENGTH:
        return text
    return f"{text[:EXCERPT_LENGTH].strip()}..."


def _label_sections(label: dict[str, Any]) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    for field in LABEL_SECTION_FIELDS:
        for value in _string_list(label.get(field)) or []:
            sections.append({"label_section": field, "text": value})
    return sections


def _hierarchy_pd_match(
    source_item: dict[str, Any],
    target_item: dict[str, Any],
    sections: list[dict[str, str]],
) -> tuple[str, str, str] | None:
    combined_categories = source_item["categories"].union(target_item["categories"])
    hierarchy = _hierarchy_assessment(combined_categories)
    if hierarchy is None:
        return None

    risk_terms = {
        "bleeding",
        "gastrointestinal",
        "hemorrhage",
        "respiratory depression",
        "sedation",
    }
    for section in sections:
        text = _normalize_whitespace(section["text"])
        text_casefolded = text.casefold()
        if any(term in text_casefolded for term in risk_terms):
            return (
                _excerpt_around_risk(text, risk_terms),
                _hierarchy_match_label(combined_categories),
                section["label_section"],
            )
    return None


def _hierarchy_match_label(categories: set[str]) -> str:
    if {"nsaid", "anticoagulant"}.issubset(categories):
        return "NSAID + anticoagulant"
    if {"opioid", "benzodiazepine"}.issubset(categories):
        return "opioid + benzodiazepine"
    if {"antiplatelet", "anticoagulant"}.issubset(categories):
        return "antiplatelet + anticoagulant"
    return "critical pharmacodynamic class pattern"


def _excerpt_around_risk(text: str, risk_terms: set[str]) -> str:
    text_casefolded = text.casefold()
    indexes = [
        text_casefolded.find(term)
        for term in risk_terms
        if text_casefolded.find(term) >= 0
    ]
    if not indexes:
        return _first_excerpt([{"label_section": LABEL_INTERACTION_FIELD, "text": text}])
    start = max(0, min(indexes) - 180)
    end = min(len(text), start + EXCERPT_LENGTH)
    excerpt = text[start:end].strip()
    if start > 0:
        excerpt = f"...{excerpt}"
    if end < len(text):
        excerpt = f"{excerpt}..."
    return excerpt


def _risk_statement(excerpt: str) -> str | None:
    sentences = _label_sentences(excerpt)
    risk_sentences = [
        sentence
        for sentence in sentences
        if any(term in sentence.casefold() for term in RISK_TERMS)
    ]
    if not risk_sentences:
        return None
    best_sentence = max(risk_sentences, key=_risk_score)
    return _clean_risk_statement(best_sentence)


def _label_sentences(text: str) -> list[str]:
    cleaned = _normalize_whitespace(text).strip(". ")
    if not cleaned:
        return []
    use_with_matches = re.findall(
        r"Use with [^:.]{1,80}:\s*[^.]{1,240}\.",
        cleaned,
        flags=re.IGNORECASE,
    )
    sentences = use_with_matches + re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", cleaned)
    return [sentence.strip(" .") for sentence in sentences if sentence.strip(" .")]


def _risk_score(sentence: str) -> int:
    normalized = sentence.casefold()
    return sum(
        (len(RISK_PRIORITY_TERMS) - index) * 10
        for index, term in enumerate(RISK_PRIORITY_TERMS)
        if term in normalized
    )


def _clean_risk_statement(sentence: str) -> str:
    cleaned = _remove_label_references(sentence).strip(" .")
    cleaned = re.sub(r"^\.\.\.", "", cleaned).strip()
    for marker in (
        "Due to additive pharmacologic effect, ",
        "7 DRUG INTERACTIONS ",
    ):
        cleaned = cleaned.replace(marker, "")
    concise = _concise_risk_phrase(cleaned)
    if concise:
        return concise
    if len(cleaned) > 360:
        cleaned = f"{cleaned[:357].rstrip()}..."
    return cleaned


def _concise_risk_phrase(sentence: str) -> str | None:
    patterns = (
        r"(Use with [^:.]{1,80}:\s*Increase the risk of [^.]{1,160})",
        r"(can increase the risk of [^.]{1,180})",
        r"(increase the risk of [^.]{1,160})",
        r"(result in [^.]{1,180})",
    )
    for pattern in patterns:
        match = re.search(pattern, sentence, flags=re.IGNORECASE)
        if not match:
            continue
        phrase = match.group(1).strip(" ,.;")
        if phrase.casefold().startswith(("can ", "increase ", "result ")):
            phrase = f"{phrase[0].upper()}{phrase[1:]}"
        return f"{phrase}."
    return None


def _remove_label_references(text: str) -> str:
    return re.sub(r"\(\s*\d+(?:\.\d+)?\s*\)", "", text)


def _string_list(value: Any) -> list[str] | None:
    if value is None:
        return None
    values = value if isinstance(value, list) else [value]
    cleaned_values = [_clean_string(item) for item in values]
    result = [item for item in cleaned_values if item is not None]
    return result or None


def _escape_phrase(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _class_name_terms(class_name: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", class_name)
    terms = {
        word
        for word in words
        if len(word) >= 5 and word not in CLASS_TERM_STOPWORDS
    }
    terms.update(_singularize(term) for term in list(terms))
    if 5 <= len(class_name) <= 80:
        terms.add(class_name)
    return {term for term in terms if len(term) >= 4}


def _class_categories(terms: set[str]) -> set[str]:
    normalized_terms = {term.casefold() for term in terms if term}
    categories: set[str] = set()
    for category, category_terms in DRUG_CLASS_CATEGORIES.items():
        if any(_category_term_matches(normalized_terms, term) for term in category_terms):
            categories.add(category)
    return categories


def _category_term_matches(terms: set[str], category_term: str) -> bool:
    normalized_category_term = category_term.casefold()
    return any(
        normalized_category_term == term
        or normalized_category_term in term
        or term in normalized_category_term
        for term in terms
    )


def _contains_term(text: str, term: str) -> bool:
    if " " in term:
        return term in text
    return re.search(rf"\b{re.escape(term)}s?\b", text) is not None


def _first_term_index(text: str, term: str) -> int:
    if " " in term:
        return text.find(term)
    match = re.search(rf"\b{re.escape(term)}s?\b", text)
    return match.start() if match else len(text)


def _singularize(term: str) -> str:
    if term.endswith("ies") and len(term) > 4:
        return f"{term[:-3]}y"
    if term.endswith("s") and len(term) > 4:
        return term[:-1]
    return term


def _normalize_term(value: Any) -> str:
    cleaned = _clean_string(value)
    return cleaned.casefold() if cleaned else ""


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None
