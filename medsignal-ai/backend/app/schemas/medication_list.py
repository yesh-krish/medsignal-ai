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
