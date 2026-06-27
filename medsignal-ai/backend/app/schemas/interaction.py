from pydantic import BaseModel


class InteractionDrugRead(BaseModel):
    rxcui: str
    name: str


class InteractionEvidenceRead(BaseModel):
    source_drug_name: str
    source_rxcui: str
    matched_drug_name: str | None = None
    matched_rxcui: str | None = None
    matched_term: str | None = None
    match_type: str
    label_section: str
    risk_statement: str | None = None
    excerpt: str


class PotentialInteractionRead(BaseModel):
    source: str
    severity: str | None
    severity_tier: str | None = None
    mechanism: str | None = None
    risk_category: str | None = None
    description: str
    drugs: list[InteractionDrugRead]
    explanation: str | None = None
    assessment_reason: str | None = None
    evidence: list[InteractionEvidenceRead] | None = None


class InteractionScreeningResponse(BaseModel):
    medication_list_id: int
    checked_rxcuis: list[str]
    interactions: list[PotentialInteractionRead]
    disclaimer: str
