from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SignalAnalysisRun(Base):
    __tablename__ = "signal_analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    drug_id: Mapped[int] = mapped_column(ForeignKey("drugs.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    comparator_scope: Mapped[str] = mapped_column(String(255), nullable=False)
    minimum_reports: Mapped[int] = mapped_column(Integer, nullable=False)
    prr_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    ror_ci_lower_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    target_total_reports: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comparator_total_reports: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SignalResult(Base):
    __tablename__ = "signal_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("signal_analysis_runs.id"), index=True
    )
    drug_id: Mapped[int] = mapped_column(ForeignKey("drugs.id"), index=True)
    reaction: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    target_with_reaction: Mapped[int] = mapped_column(Integer, nullable=False)
    target_without_reaction: Mapped[int] = mapped_column(Integer, nullable=False)
    comparator_with_reaction: Mapped[int] = mapped_column(Integer, nullable=False)
    comparator_without_reaction: Mapped[int] = mapped_column(Integer, nullable=False)
    prr: Mapped[float] = mapped_column(Float, nullable=False)
    ror: Mapped[float] = mapped_column(Float, nullable=False)
    ror_ci_lower: Mapped[float] = mapped_column(Float, nullable=False)
    ror_ci_upper: Mapped[float] = mapped_column(Float, nullable=False)
    is_potential_signal: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, nullable=False
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
