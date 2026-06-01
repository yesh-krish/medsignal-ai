from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AdverseEvent(Base):
    __tablename__ = "adverse_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    drug_id: Mapped[int] = mapped_column(ForeignKey("drugs.id"), index=True)
    reaction: Mapped[str | None] = mapped_column(String(255), index=True)
    serious: Mapped[bool] = mapped_column(default=False, nullable=False)
    outcome: Mapped[str | None] = mapped_column(String(255))
    report_date: Mapped[date | None] = mapped_column(Date, index=True)
    patient_age: Mapped[float | None] = mapped_column(Float)
    patient_sex: Mapped[str | None] = mapped_column(String(32), index=True)
    raw_event_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
