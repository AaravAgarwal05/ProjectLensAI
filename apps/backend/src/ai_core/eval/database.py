"""SQLAlchemy ORM model for persisted evaluation runs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base


class EvalRunModel(Base):
    """Database model for an evaluation run (RAG quality benchmark)."""

    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    judge_provider: Mapped[str] = mapped_column(String(32), nullable=False)
    judge_model: Mapped[str] = mapped_column(String(64), nullable=False)
    llm_model: Mapped[str] = mapped_column(String(64), nullable=True)
    embedding_model: Mapped[str] = mapped_column(String(64), nullable=True)
    retrieval_top_k: Mapped[int] = mapped_column(Integer, nullable=True)
    mmr_lambda: Mapped[float] = mapped_column(Float, nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=True)
    overall: Mapped[float] = mapped_column(Float, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    results: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
