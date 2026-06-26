from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IngestionRunRead(BaseModel):
    id: int
    drug_id: int
    source: str
    status: str
    query: str
    requested_reports: int
    fetched_reports: int
    saved_reaction_rows: int
    duplicate_reports_skipped: int
    source_last_updated: str | None
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
