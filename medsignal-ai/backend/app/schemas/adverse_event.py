from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AdverseEventRead(BaseModel):
    id: int
    drug_id: int
    ingestion_run_id: int | None
    safety_report_id: str | None
    case_version: int | None
    reaction_index: int | None
    reaction: str | None
    serious: bool
    outcome: str | None
    report_date: date | None
    patient_age: float | None
    patient_sex: str | None
    raw_event_json: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReactionCount(BaseModel):
    reaction: str
    count: int


class EventTrends(BaseModel):
    top_reported_reactions: list[ReactionCount]
    reports_by_year: dict[str, int]
    seriousness_breakdown: dict[str, int]
    sex_breakdown: dict[str, int]
    total_reports: int
