from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SafetyAlertRead(BaseModel):
    id: int
    drug_id: int
    alert_type: str
    reaction: str | None
    baseline_count: int
    current_count: int
    percent_change: float
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
