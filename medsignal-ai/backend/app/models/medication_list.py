from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.drug import Drug


class MedicationList(Base):
    __tablename__ = "medication_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    items: Mapped[list["MedicationListItem"]] = relationship(
        back_populates="medication_list",
        cascade="all, delete-orphan",
    )
    risk_profile: Mapped["MedicationRiskProfile | None"] = relationship(
        back_populates="medication_list",
        cascade="all, delete-orphan",
        uselist=False,
    )


class MedicationListItem(Base):
    __tablename__ = "medication_list_items"
    __table_args__ = (
        UniqueConstraint("medication_list_id", "drug_id", name="uq_med_list_drug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    medication_list_id: Mapped[int] = mapped_column(
        ForeignKey("medication_lists.id"), index=True, nullable=False
    )
    drug_id: Mapped[int] = mapped_column(ForeignKey("drugs.id"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    medication_list: Mapped[MedicationList] = relationship(back_populates="items")
    drug: Mapped[Drug] = relationship()


class MedicationRiskProfile(Base):
    __tablename__ = "medication_risk_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    medication_list_id: Mapped[int] = mapped_column(
        ForeignKey("medication_lists.id"), unique=True, index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    medication_list: Mapped[MedicationList] = relationship(back_populates="risk_profile")
    factors: Mapped[list["MedicationRiskFactor"]] = relationship(
        back_populates="risk_profile",
        cascade="all, delete-orphan",
    )


class MedicationRiskFactor(Base):
    __tablename__ = "medication_risk_factors"
    __table_args__ = (
        UniqueConstraint("risk_profile_id", "factor_key", name="uq_risk_profile_factor"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    risk_profile_id: Mapped[int] = mapped_column(
        ForeignKey("medication_risk_profiles.id"), index=True, nullable=False
    )
    factor_key: Mapped[str] = mapped_column(String(80), nullable=False)
    is_present: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    risk_profile: Mapped[MedicationRiskProfile] = relationship(back_populates="factors")
