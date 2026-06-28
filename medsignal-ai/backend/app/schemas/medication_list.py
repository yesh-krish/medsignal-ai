from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.drug import DrugSearchResult


class MedicationListItemCreate(BaseModel):
    drug_id: int


class MedicationListItemRead(BaseModel):
    id: int
    medication_list_id: int
    drug_id: int
    drug: DrugSearchResult
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MedicationListRead(BaseModel):
    id: int
    name: str
    items: list[MedicationListItemRead]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MedicationRiskFactorAnswer(BaseModel):
    factor_key: str
    is_present: bool = False
    note: str | None = None


class MedicationRiskFactorRead(BaseModel):
    factor_key: str
    label: str
    help_text: str
    input_type: str
    is_present: bool
    note: str | None


class MedicationRiskProfileUpdate(BaseModel):
    factors: list[MedicationRiskFactorAnswer]


class MedicationRiskDiscussionItem(BaseModel):
    factor_key: str
    label: str
    concern: str
    connected_categories: list[str]
    matched_medications: list[str]


class MedicationRiskProfileRead(BaseModel):
    id: int
    medication_list_id: int
    factors: list[MedicationRiskFactorRead]
    factors_to_discuss: list[MedicationRiskDiscussionItem]
    disclaimer: str
    created_at: datetime
    updated_at: datetime
