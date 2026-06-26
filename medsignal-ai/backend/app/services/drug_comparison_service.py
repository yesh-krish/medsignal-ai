from datetime import date

from app.models.drug import Drug
from app.models.drug_label import DrugLabel
from app.services import openfda_event_service, openfda_label_service


COMPARISON_DISCLAIMER = (
    "This comparison is educational and uses reported adverse events and FDA "
    "label sections. Report counts cannot establish which medication is safer "
    "and do not prove that a medication caused an event."
)
COMPARISON_YEARS = 8


def build_drug_comparison(left_drug: Drug, right_drug: Drug, db):
    start_year = max(2004, date.today().year - COMPARISON_YEARS + 1)
    left_trends = openfda_event_service.fetch_reported_adverse_event_trends(
        _normalized_name(left_drug), start_year=start_year
    )
    right_trends = openfda_event_service.fetch_reported_adverse_event_trends(
        _normalized_name(right_drug), start_year=start_year
    )
    left_label = _fetch_label(left_drug, db)
    right_label = _fetch_label(right_drug, db)

    return {
        "left": {
            "drug": left_drug,
            "trends": left_trends,
            "label": left_label,
        },
        "right": {
            "drug": right_drug,
            "trends": right_trends,
            "label": right_label,
        },
        "shared_top_reported_reactions": _shared_reactions(
            left_trends["top_reported_reactions"],
            right_trends["top_reported_reactions"],
        ),
        "label_section_comparison": _compare_label_sections(left_label, right_label),
        "disclaimer": COMPARISON_DISCLAIMER,
    }


def _normalized_name(drug: Drug) -> str:
    if not drug.normalized_name:
        raise ValueError("Drug does not have a normalized name")
    return drug.normalized_name


def _fetch_label(drug: Drug, db) -> DrugLabel | None:
    saved_label = openfda_label_service.get_saved_drug_label(drug.id, db)
    if saved_label is not None:
        return saved_label
    return openfda_label_service.fetch_and_save_drug_label(
        _normalized_name(drug), drug.id, db
    )


def _shared_reactions(
    left_reactions: list[dict],
    right_reactions: list[dict],
) -> list[dict]:
    right_by_reaction = {
        str(item["reaction"]).casefold(): item
        for item in right_reactions
        if item.get("reaction")
    }
    shared = []
    for left_item in left_reactions:
        reaction = left_item.get("reaction")
        if not reaction:
            continue
        right_item = right_by_reaction.get(str(reaction).casefold())
        if right_item is None:
            continue
        left_count = int(left_item.get("count", 0))
        right_count = int(right_item.get("count", 0))
        shared.append(
            {
                "reaction": str(reaction),
                "left_count": left_count,
                "right_count": right_count,
                "absolute_difference": abs(left_count - right_count),
            }
        )
    return sorted(shared, key=lambda item: item["absolute_difference"], reverse=True)


def _compare_label_sections(
    left_label: DrugLabel | None,
    right_label: DrugLabel | None,
) -> list[dict]:
    sections = [
        ("FDA label warnings", "warnings"),
        ("FDA adverse reactions", "adverse_reactions"),
        ("FDA contraindications", "contraindications"),
        ("Boxed warning", "boxed_warning"),
    ]
    return [
        {
            "section": title,
            "left_available": bool(_section_items(left_label, field)),
            "right_available": bool(_section_items(right_label, field)),
            "left_count": len(_section_items(left_label, field)),
            "right_count": len(_section_items(right_label, field)),
        }
        for title, field in sections
    ]


def _section_items(label: DrugLabel | None, field: str) -> list[str]:
    if label is None:
        return []
    value = getattr(label, field)
    return value or []
