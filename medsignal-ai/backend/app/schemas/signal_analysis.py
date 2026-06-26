from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SignalResultRead(BaseModel):
    id: int
    run_id: int
    drug_id: int
    reaction: str
    target_with_reaction: int
    target_without_reaction: int
    comparator_with_reaction: int
    comparator_without_reaction: int
    prr: float
    ror: float
    ror_ci_lower: float
    ror_ci_upper: float
    is_potential_signal: bool
    explanation: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SignalAnalysisRunRead(BaseModel):
    id: int
    drug_id: int
    status: str
    source: str
    comparator_scope: str
    minimum_reports: int
    prr_threshold: float
    ror_ci_lower_threshold: float
    target_total_reports: int
    comparator_total_reports: int
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class SignalAnalysisResponse(BaseModel):
    run: SignalAnalysisRunRead
    results: list[SignalResultRead]
