"""Vector-store factory — create providers from configuration."""

from __future__ import annotations

from typing import Any

from src.ai_core.vector_store.base import VectorStore
from src.ai_core.vector_store.configuration import VectorStoreConfiguration
from src.ai_core.vector_store.registry import VectorStoreRegistry

_STORE_ALIASES: dict[str, str] = {
    "chroma": "chroma",
    "chromadb": "chroma",
    "pgvector": "pgvector",
    "postgres": "pgvector",
    "default": "chroma",
}


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
