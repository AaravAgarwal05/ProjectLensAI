"""Vector-store factory — create providers from configuration."""

from __future__ import annotations

from typing import Any

from src.ai_core.vector_store.base import VectorStore
from src.ai_core.vector_store.configuration import VectorStoreConfiguration
from src.ai_core.vector_store.providers.chroma_store import ChromaVectorStore
from src.ai_core.vector_store.providers.pgvector_store import PgVectorStore
from src.ai_core.vector_store.registry import VectorStoreRegistry

_STORE_ALIASES: dict[str, str] = {
    "chroma": "chroma",
    "chromadb": "chroma",
    "pgvector": "pgvector",
    "postgres": "pgvector",
    "default": "chroma",
}


def build_vector_store(settings: Any | None = None) -> VectorStore:
    """Build the runtime retrieval vector store for the configured provider.

    This is the **direct singleton** used by the live chat/search paths
    (``VECTOR_STORE_PROVIDER``: ``chroma`` in dev, ``pgvector`` in prod).
    The registry/factory path above is used by the indexing engine only.

    Args:
        settings: Optional ``AppSettings``. Resolved if omitted.

    Returns:
        A configured ``VectorStore`` instance.
    """
    if settings is None:
        from src.config.settings import get_settings

        settings = get_settings()
    provider = _STORE_ALIASES.get(
        getattr(settings, "VECTOR_STORE_PROVIDER", "chroma").lower().strip(), "chroma"
    )
    if provider == "pgvector":
        # asyncpg DSN -> plain postgresql DSN for the store's own connection pool.
        dsn = settings.DATABASE_URL.replace("+asyncpg", "")
        return PgVectorStore(dsn=dsn)
    return ChromaVectorStore(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
    )


class VectorStoreFactory:
    """Creates vector-store instances from configuration."""

    def __init__(self, registry: VectorStoreRegistry | None = None) -> None:
        self._registry = registry or VectorStoreRegistry()

    @property
    def registry(self) -> VectorStoreRegistry:
        return self._registry

    def create(
        self,
        name: str,
        /,
        **kwargs: Any,
    ) -> VectorStore:
        """Create (or retrieve a cached) store by name."""
        resolved = _STORE_ALIASES.get(name.lower().strip(), name)
        return self._registry.get(resolved, **kwargs)

    def create_from_config(
        self,
        config: VectorStoreConfiguration,
        /,
    ) -> VectorStore:
        """Create a store from a ``VectorStoreConfiguration``."""
        store_name = config.store
        store = self._registry.get(store_name)
        store.configure(config.extra)
        return store

    def create_all(self, **kwargs: Any) -> list[VectorStore]:
        """Return one instance of every registered store."""
        return self._registry.create_all(**kwargs)

    def available_stores(self) -> list[str]:
        """Return the list of registered store names."""
        return self._registry.list_names()
