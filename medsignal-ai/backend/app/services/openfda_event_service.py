from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Any

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.adverse_event import AdverseEvent


class OpenFDAUpstreamError(Exception):
    pass


class OpenFDATimeoutError(Exception):
    pass


@dataclass(frozen=True)
class ExtractedReportedAdverseEvent:
    reaction: str | None
    serious: bool
    outcome: str | None
    report_date: date | None
    patient_age: float | None
    patient_sex: str | None
    raw_event_json: dict[str, Any]


def fetch_and_save_reported_adverse_events(
    normalized_drug_name: str,
    drug_id: int,
    db: Session,
    limit: int = 25,
) -> list[AdverseEvent]:
    cleaned_name = normalized_drug_name.strip()
    if not cleaned_name:
        raise ValueError("Normalized drug name must not be empty")

    results = _query_openfda(cleaned_name, limit=limit)
    extracted_events: list[ExtractedReportedAdverseEvent] = []
    for event in results:
        if _event_matches_drug(event, cleaned_name):
            extracted_events.extend(extract_reported_adverse_events(event))

    db.execute(delete(AdverseEvent).where(AdverseEvent.drug_id == drug_id))
    saved_events = [
        AdverseEvent(
            drug_id=drug_id,
            reaction=event.reaction,
            serious=event.serious,
            outcome=event.outcome,
            report_date=event.report_date,
            patient_age=event.patient_age,
            patient_sex=event.patient_sex,
            raw_event_json=event.raw_event_json,
        )
        for event in extracted_events
    ]
    db.add_all(saved_events)
    db.commit()
    for event in saved_events:
        db.refresh(event)
    return saved_events


def get_saved_reported_adverse_events(drug_id: int, db: Session) -> list[AdverseEvent]:
    return list(
        db.scalars(
            select(AdverseEvent)
            .where(AdverseEvent.drug_id == drug_id)
            .order_by(AdverseEvent.id)
        )
    )


def build_reported_adverse_event_trends(events: list[AdverseEvent]) -> dict[str, Any]:
    reaction_counts = Counter(
        event.reaction for event in events if event.reaction is not None
    )
    unique_reports = _unique_report_events(events)
    years = Counter(
        str(event.report_date.year)
        for event in unique_reports
        if event.report_date is not None
    )
    seriousness = Counter(
        "serious" if event.serious else "not_serious" for event in unique_reports
    )
    sex = Counter(event.patient_sex or "unknown" for event in unique_reports)

    return {
        "top_reported_reactions": [
            {"reaction": reaction, "count": count}
            for reaction, count in reaction_counts.most_common(10)
        ],
        "reports_by_year": dict(sorted(years.items())),
        "seriousness_breakdown": dict(seriousness),
        "sex_breakdown": dict(sex),
        "total_reports": len(unique_reports),
    }


def extract_reported_adverse_events(
    event: dict[str, Any],
) -> list[ExtractedReportedAdverseEvent]:
    patient = event.get("patient") or {}
    reactions = patient.get("reaction") or []
    if not reactions:
        reactions = [{}]

    return [
        ExtractedReportedAdverseEvent(
            reaction=_clean_string(reaction.get("reactionmeddrapt")),
            serious=_parse_serious(event.get("serious")),
            outcome=_clean_string(reaction.get("reactionoutcome")),
            report_date=_parse_report_date(event.get("receivedate")),
            patient_age=_parse_patient_age(patient.get("patientonsetage")),
            patient_sex=_parse_patient_sex(patient.get("patientsex")),
            raw_event_json=event,
        )
        for reaction in reactions
    ]


def _query_openfda(normalized_drug_name: str, limit: int) -> list[dict[str, Any]]:
    settings = get_settings()
    try:
        with httpx.Client(timeout=settings.openfda_timeout_seconds) as client:
            response = client.get(
                f"{settings.openfda_base_url}/drug/event.json",
                params={
                    "search": f'patient.drug.medicinalproduct:"{normalized_drug_name}"',
                    "limit": str(limit),
                },
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException as exc:
        raise OpenFDATimeoutError("openFDA request timed out") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise OpenFDAUpstreamError("openFDA request failed") from exc

    return data.get("results", [])


def _event_matches_drug(event: dict[str, Any], normalized_drug_name: str) -> bool:
    normalized = normalized_drug_name.casefold()
    drugs = (event.get("patient") or {}).get("drug") or []
    for drug in drugs:
        medicinal_product = _clean_string(drug.get("medicinalproduct"))
        if medicinal_product is None:
            continue
        candidate = medicinal_product.casefold()
        if normalized in candidate or candidate in normalized:
            return True
    return False


def _parse_report_date(value: Any) -> date | None:
    value = _clean_string(value)
    if value is None or len(value) != 8:
        return None
    try:
        return date(int(value[0:4]), int(value[4:6]), int(value[6:8]))
    except ValueError:
        return None


def _parse_serious(value: Any) -> bool:
    return str(value) == "1"


def _parse_patient_age(value: Any) -> float | None:
    value = _clean_string(value)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_patient_sex(value: Any) -> str | None:
    return {"1": "male", "2": "female", "0": "unknown"}.get(str(value))


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _unique_report_events(events: list[AdverseEvent]) -> list[AdverseEvent]:
    unique_events: dict[str, AdverseEvent] = {}
    for index, event in enumerate(events):
        report_id = event.raw_event_json.get("safetyreportid") if event.raw_event_json else None
        key = str(report_id or event.id or f"event-{index}")
        unique_events.setdefault(key, event)
    return list(unique_events.values())
