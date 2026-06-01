from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DrugLabelRead(BaseModel):
    id: int
    drug_id: int
    set_id: str | None
    brand_name: list[str] | None
    generic_name: list[str] | None
    warnings: list[str] | None
    adverse_reactions: list[str] | None
    contraindications: list[str] | None
    indications_and_usage: list[str] | None
    boxed_warning: list[str] | None
    raw_label_json: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
