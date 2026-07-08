"""Vector-store configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VectorStoreConfiguration:
    """Configuration for vector-store providers.

    Attributes:
        store: Default store name (``"chroma"``).
        collection_name: Default collection name (``"default"``).
        batch_size: Max documents per batch (default 100).
        chroma_path: ChromaDB persistence path (optional).
        pgvector_dsn: PostgreSQL connection string (optional).
        extra: Store-specific overrides.
    """

    store: str = "chroma"
    collection_name: str = "default"
    batch_size: int = 100
    chroma_path: str | None = None
    pgvector_dsn: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def default(cls) -> VectorStoreConfiguration:
        """Return a default configuration."""
        return cls()

    def merge(self, overrides: dict[str, Any]) -> VectorStoreConfiguration:
        """Return a new configuration with *overrides* applied."""
        merged = {**self.__dict__, **overrides}
        return VectorStoreConfiguration(**merged)
