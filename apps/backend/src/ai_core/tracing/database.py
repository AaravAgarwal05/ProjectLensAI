"""SQLAlchemy ORM model for request traces."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base


class RequestTraceModel(Base):
    """Database model for a single request trace."""

    __tablename__ = "request_traces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    prompt_version: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    prompt_hash: Mapped[str | None] = mapped_column(String(32), nullable=True)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stages: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    counts: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )
