"""User ORM model for authentication."""

import json

from sqlalchemy import Boolean, Column, Integer, String, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB

from src.database.base import Base
from src.database.mixins import TimestampMixin, UUIDMixin

# --- SQLite-safe JSON column ---


class JSONColumn(TypeDecorator):
    """Generic JSON column — uses JSONB on PostgreSQL, TEXT on SQLite."""

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_dialect_impl(self.impl)

    def process_bind_param(self, value, dialect):
        if dialect.name == "postgresql":
            return value
        return json.dumps(value) if value is not None else None

    def process_result_value(self, value, dialect):
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            return json.loads(value)
        return {}


# --- Default preferences ---

DEFAULT_PREFERENCES = {
    "chunking_strategy": "heading_aware",
    "llm_provider": "opencode_zen",
    "llm_model": "deepseek-v4-flash-free",
    "retrieval_strategy": "hybrid",
    "embedding_provider": "ollama",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "min_chunk_size": 100,
    "embedding_model": "nomic-embed-text",
    "top_k": 5,
}


class User(UUIDMixin, TimestampMixin, Base):
    """Registered user account."""

    __tablename__ = "users"
    __allow_unmapped__ = True

    email: Column[str] = Column(String(255), nullable=False, unique=True, index=True)
    name: Column[str] = Column(String(255), nullable=False)
    hashed_password: Column[str] = Column(String(255), nullable=False)
    role: Column[str] = Column(String(50), nullable=False, default="user")
    is_active: Column[bool] = Column(Boolean, nullable=False, default=True)
    token_version: Column[int] = Column(Integer, nullable=False, default=0, server_default="0")
    preferences: Column[dict] = Column(
        JSONColumn(),
        nullable=False,
        default=lambda: dict(DEFAULT_PREFERENCES),
    )
