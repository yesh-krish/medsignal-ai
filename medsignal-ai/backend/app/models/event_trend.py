from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EventTrend(Base):
    __tablename__ = "event_trends"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    drug_id: Mapped[int] = mapped_column(
        ForeignKey("drugs.id"), index=True, unique=True
    )
    trends_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
