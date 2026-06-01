from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DrugBase(BaseModel):
    rxcui: str | None = None
    input_name: str
    normalized_name: str | None = None
    synonym: str | None = None
    tty: str | None = None


class DrugCreate(DrugBase):
    pass


class DrugRead(DrugBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DrugSearchResult(DrugBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
