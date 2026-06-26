from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.adverse_event import AdverseEvent
from app.models.ingestion_run import IngestionRun


class OpenFDAUpstreamError(Exception):
    pass


class OpenFDATimeoutError(Exception):
    pass


@dataclass(frozen=True)
class ExtractedReportedAdverseEvent:
    safety_report_id: str | None
    case_version: int | None
    reaction_index: int
    reaction: str | None
    serious: bool
    outcome: str | None
    report_date: date | None
    patient_age: float | None
    patient_sex: str | None
    raw_event_json: dict[str, Any]


@dataclass(frozen=True)
class ReactionSignalCount:
    reaction: str
    target_count: int
    all_reaction_count: int


@dataclass(frozen=True)
class SignalCountData:
    target_total: int
    all_reports_total: int
    reactions: list[ReactionSignalCount]


def fetch_and_save_reported_adverse_events(
    normalized_drug_name: str,
    drug_id: int,
    db: Session,
    limit: int = 25,
) -> list[AdverseEvent]:
    cleaned_name = normalized_drug_name.strip()
    if not cleaned_name:
        raise ValueError("Normalized drug name must not be empty")

    query = _openfda_drug_search(cleaned_name)
    run = IngestionRun(
        drug_id=drug_id,
        source="openFDA FAERS",
        status="running",
        query=query,
        requested_reports=limit,
        fetched_reports=0,
        saved_reaction_rows=0,
        duplicate_reports_skipped=0,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        results, source_last_updated = _query_openfda_paginated(
            cleaned_name, limit=limit
        )
        latest_reports, duplicates_skipped = _deduplicate_latest_case_versions(
            results
        )
        extracted_events: list[ExtractedReportedAdverseEvent] = []
        for event in latest_reports:
            if _event_matches_drug(event, cleaned_name):
                extracted_events.extend(extract_reported_adverse_events(event))

        db.execute(delete(AdverseEvent).where(AdverseEvent.drug_id == drug_id))
        saved_events = [
            AdverseEvent(
                drug_id=drug_id,
                ingestion_run_id=run.id,
                safety_report_id=event.safety_report_id,
                case_version=event.case_version,
                reaction_index=event.reaction_index,
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
        run.status = "succeeded"
        run.fetched_reports = len(results)
        run.saved_reaction_rows = len(saved_events)
        run.duplicate_reports_skipped = duplicates_skipped
        run.source_last_updated = source_last_updated
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        for event in saved_events:
            db.refresh(event)
        return saved_events
    except Exception as exc:
        db.rollback()
        failed_run = db.get(IngestionRun, run.id)
        if failed_run is not None:
            failed_run.status = "failed"
            failed_run.error_message = str(exc)[:2000]
            failed_run.completed_at = datetime.now(timezone.utc)
            db.commit()
        raise


def get_saved_reported_adverse_events(drug_id: int, db: Session) -> list[AdverseEvent]:
    return list(
        db.scalars(
            select(AdverseEvent)
            .where(AdverseEvent.drug_id == drug_id)
            .order_by(AdverseEvent.id)
        )
    )


def get_latest_ingestion_run(drug_id: int, db: Session) -> IngestionRun | None:
    return db.scalar(
        select(IngestionRun)
        .where(IngestionRun.drug_id == drug_id)
        .order_by(IngestionRun.started_at.desc(), IngestionRun.id.desc())
        .limit(1)
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


def fetch_reported_adverse_event_trends(
    normalized_drug_name: str,
    start_year: int = 2004,
    end_year: int | None = None,
) -> dict[str, Any]:
    cleaned_name = normalized_drug_name.strip()
    if not cleaned_name:
        raise ValueError("Normalized drug name must not be empty")

    reports_by_year = _query_openfda_yearly_totals(
        cleaned_name,
        start_year=start_year,
        end_year=end_year or date.today().year,
    )
    reaction_counts = _query_openfda_counts(
        cleaned_name, "patient.reaction.reactionmeddrapt.exact", limit=10
    )
    seriousness_counts = _query_openfda_counts(cleaned_name, "serious", limit=10)
    sex_counts = _query_openfda_counts(cleaned_name, "patient.patientsex", limit=10)

    return {
        "top_reported_reactions": [
            {"reaction": str(item.get("term")), "count": int(item.get("count", 0))}
            for item in reaction_counts
            if item.get("term")
        ],
        "reports_by_year": reports_by_year,
        "seriousness_breakdown": _map_seriousness_counts(seriousness_counts),
        "sex_breakdown": _map_sex_counts(sex_counts),
        "total_reports": _query_openfda_total(cleaned_name),
    }


def fetch_signal_count_data(
    normalized_drug_name: str,
    reaction_limit: int = 10,
) -> SignalCountData:
    cleaned_name = normalized_drug_name.strip()
    if not cleaned_name:
        raise ValueError("Normalized drug name must not be empty")

    target_total = _query_openfda_total(cleaned_name)
    all_reports_total = _query_openfda_total_for_search(None)
    target_reactions = _query_openfda_counts(
        cleaned_name,
        "patient.reaction.reactionmeddrapt.exact",
        limit=reaction_limit,
    )
    reactions: list[ReactionSignalCount] = []
    for item in target_reactions:
        reaction = _clean_string(item.get("term"))
        if reaction is None:
            continue
        reaction_search = (
            "patient.reaction.reactionmeddrapt.exact:"
            f'"{_escape_openfda_phrase(reaction)}"'
        )
        reactions.append(
            ReactionSignalCount(
                reaction=reaction,
                target_count=int(item.get("count", 0)),
                all_reaction_count=_query_openfda_total_for_search(reaction_search),
            )
        )

    return SignalCountData(
        target_total=target_total,
        all_reports_total=all_reports_total,
        reactions=reactions,
    )


def extract_reported_adverse_events(
    event: dict[str, Any],
) -> list[ExtractedReportedAdverseEvent]:
    patient = event.get("patient") or {}
    reactions = patient.get("reaction") or []
    if not reactions:
        reactions = [{}]

    safety_report_id = _clean_string(event.get("safetyreportid"))
    case_version = _parse_case_version(event.get("safetyreportversion"))

    return [
        ExtractedReportedAdverseEvent(
            safety_report_id=safety_report_id,
            case_version=case_version,
            reaction_index=index,
            reaction=_clean_string(reaction.get("reactionmeddrapt")),
            serious=_parse_serious(event.get("serious")),
            outcome=_clean_string(reaction.get("reactionoutcome")),
            report_date=_parse_report_date(event.get("receivedate")),
            patient_age=_parse_patient_age(patient.get("patientonsetage")),
            patient_sex=_parse_patient_sex(patient.get("patientsex")),
            raw_event_json=event,
        )
        for index, reaction in enumerate(reactions)
    ]


def _query_openfda_paginated(
    normalized_drug_name: str,
    limit: int,
    page_size: int = 100,
) -> tuple[list[dict[str, Any]], str | None]:
    results: list[dict[str, Any]] = []
    source_last_updated: str | None = None

    while len(results) < limit:
        current_limit = min(page_size, limit - len(results))
        data = _openfda_get_json(
            normalized_drug_name,
            params={"limit": str(current_limit), "skip": str(len(results))},
        )
        page = data.get("results", [])
        source_last_updated = source_last_updated or _clean_string(
            data.get("meta", {}).get("last_updated")
        )
        results.extend(page)
        if len(page) < current_limit:
            break

    return results, source_last_updated


def _query_openfda_counts(
    normalized_drug_name: str,
    count_field: str,
    limit: int,
) -> list[dict[str, Any]]:
    data = _openfda_get_json(
        normalized_drug_name,
        params={"count": count_field, "limit": str(limit)},
    )
    return data.get("results", [])


def _query_openfda_total(normalized_drug_name: str) -> int:
    data = _openfda_get_json(normalized_drug_name, params={"limit": "1"})
    return int(data.get("meta", {}).get("results", {}).get("total", 0))


def _query_openfda_total_for_search(search_query: str | None) -> int:
    data = _openfda_get_json_for_search(search_query, params={"limit": "1"})
    return int(data.get("meta", {}).get("results", {}).get("total", 0))


def _query_openfda_yearly_totals(
    normalized_drug_name: str,
    start_year: int,
    end_year: int,
) -> dict[str, int]:
    yearly_totals: dict[str, int] = {}
    for year in range(start_year, end_year + 1):
        search_query = (
            _openfda_drug_search(normalized_drug_name)
            + f" AND receivedate:[{year}0101 TO {year}1231]"
        )
        data = _openfda_get_json(
            normalized_drug_name,
            params={"limit": "1"},
            search_query=search_query,
        )
        total = int(data.get("meta", {}).get("results", {}).get("total", 0))
        if total > 0:
            yearly_totals[str(year)] = total
    return yearly_totals


def _openfda_get_json(
    normalized_drug_name: str,
    params: dict[str, str],
    search_query: str | None = None,
) -> dict[str, Any]:
    return _openfda_get_json_for_search(
        search_query or _openfda_drug_search(normalized_drug_name),
        params,
    )


def _openfda_get_json_for_search(
    search_query: str | None,
    params: dict[str, str],
) -> dict[str, Any]:
    settings = get_settings()
    request_params = dict(params)
    if search_query:
        request_params["search"] = search_query
    try:
        with httpx.Client(timeout=settings.openfda_timeout_seconds) as client:
            response = client.get(
                f"{settings.openfda_base_url}/drug/event.json",
                params=request_params,
            )
            if response.status_code == 404:
                return {}
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as exc:
        raise OpenFDATimeoutError("openFDA request timed out") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise OpenFDAUpstreamError("openFDA request failed") from exc


def _openfda_drug_search(normalized_drug_name: str) -> str:
    return f'patient.drug.medicinalproduct:"{normalized_drug_name}"'


def _escape_openfda_phrase(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


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


def _parse_case_version(value: Any) -> int | None:
    cleaned = _clean_string(value)
    if cleaned is None:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _deduplicate_latest_case_versions(
    events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    latest_by_report: dict[str, dict[str, Any]] = {}
    reports_without_ids: list[dict[str, Any]] = []

    for event in events:
        report_id = _clean_string(event.get("safetyreportid"))
        if report_id is None:
            reports_without_ids.append(event)
            continue

        existing = latest_by_report.get(report_id)
        if existing is None or _case_version_sort_value(event) >= _case_version_sort_value(
            existing
        ):
            latest_by_report[report_id] = event

    deduplicated = [*latest_by_report.values(), *reports_without_ids]
    return deduplicated, len(events) - len(deduplicated)


def _case_version_sort_value(event: dict[str, Any]) -> int:
    return _parse_case_version(event.get("safetyreportversion")) or 0


def _unique_report_events(events: list[AdverseEvent]) -> list[AdverseEvent]:
    unique_events: dict[str, AdverseEvent] = {}
    for index, event in enumerate(events):
        report_id = event.raw_event_json.get("safetyreportid") if event.raw_event_json else None
        key = str(report_id or event.id or f"event-{index}")
        unique_events.setdefault(key, event)
    return list(unique_events.values())


def _map_seriousness_counts(counts: list[dict[str, Any]]) -> dict[str, int]:
    mapped: Counter[str] = Counter()
    for item in counts:
        key = "serious" if str(item.get("term")) == "1" else "not_serious"
        mapped[key] += int(item.get("count", 0))
    return dict(mapped)


def _map_sex_counts(counts: list[dict[str, Any]]) -> dict[str, int]:
    labels = {"1": "male", "2": "female", "0": "unknown"}
    mapped: Counter[str] = Counter()
    for item in counts:
        key = labels.get(str(item.get("term")), "unknown")
        mapped[key] += int(item.get("count", 0))
    return dict(mapped)
