from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SafetySummaryRead(BaseModel):
    id: int
    drug_id: int
    summary_text: str
    model_name: str
    input_length: int
    output_length: int
    latency_ms: int
    mlflow_run_id: str | None
    disclaimer: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
