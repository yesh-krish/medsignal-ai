from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    drug_id: Mapped[int] = mapped_column(ForeignKey("drugs.id"), index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    requested_reports: Mapped[int] = mapped_column(Integer, nullable=False)
    fetched_reports: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    saved_reaction_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_reports_skipped: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    source_last_updated: Mapped[str | None] = mapped_column(String(32))
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
