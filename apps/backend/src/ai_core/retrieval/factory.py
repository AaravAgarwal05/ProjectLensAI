"""Retriever factory — create retrievers from configuration."""

from __future__ import annotations

from typing import Any

from src.ai_core.retrieval.base import Retriever
from src.ai_core.retrieval.configuration import RetrieverConfiguration
from src.ai_core.retrieval.registry import RetrieverRegistry

_RETRIEVER_ALIASES: dict[str, str] = {
    "dense": "dense",
    "dense_retriever": "dense",
    "hybrid": "hybrid",
    "hybrid_retriever": "hybrid",
    "multi_query": "multi_query",
    "multi-query": "multi_query",
    "multiquery": "multi_query",
    "default": "dense",
}


class RetrieverFactory:
    """Creates retriever instances from configuration."""

    def __init__(self, registry: RetrieverRegistry | None = None) -> None:
        self._registry = registry or RetrieverRegistry()

    @property
    def registry(self) -> RetrieverRegistry:
        return self._registry

    def create(self, name: str, /, **kwargs: Any) -> Retriever:
        resolved = _RETRIEVER_ALIASES.get(name.lower().strip(), name)
        return self._registry.get(resolved, **kwargs)

    def create_from_config(self, config: RetrieverConfiguration, /) -> Retriever:
        retriever_name = config.retriever
        retriever = self._registry.get(retriever_name)
        retriever.configure(config.extra)
        return retriever

    def create_all(self, **kwargs: Any) -> list[Retriever]:
        return self._registry.create_all(**kwargs)

    def available_retrievers(self) -> list[str]:
        return self._registry.list_names()
