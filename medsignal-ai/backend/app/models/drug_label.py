from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DrugLabel(Base):
    __tablename__ = "drug_labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    drug_id: Mapped[int] = mapped_column(ForeignKey("drugs.id"), index=True)
    set_id: Mapped[str | None] = mapped_column(String(255), index=True)
    brand_name: Mapped[list[str] | None] = mapped_column(JSON)
    generic_name: Mapped[list[str] | None] = mapped_column(JSON)
    warnings: Mapped[list[str] | None] = mapped_column(JSON)
    adverse_reactions: Mapped[list[str] | None] = mapped_column(JSON)
    contraindications: Mapped[list[str] | None] = mapped_column(JSON)
    indications_and_usage: Mapped[list[str] | None] = mapped_column(JSON)
    boxed_warning: Mapped[list[str] | None] = mapped_column(JSON)
    raw_label_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
