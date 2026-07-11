"""Reranker factory — create rerankers from configuration."""

from __future__ import annotations

from typing import Any

from src.ai_core.retrieval.reranking.base import Reranker
from src.ai_core.retrieval.reranking.registry import RerankerRegistry

_RERANKER_ALIASES: dict[str, str] = {
    "none": "none",
    "no_reranker": "none",
    "no-reranker": "none",
    "cross_encoder": "cross_encoder",
    "cross-encoder": "cross_encoder",
    "crossencoder": "cross_encoder",
    "default": "none",
}


class RerankerFactory:
    """Creates reranker instances from configuration."""

    def __init__(self, registry: RerankerRegistry | None = None) -> None:
        self._registry = registry or RerankerRegistry()

    @property
    def registry(self) -> RerankerRegistry:
        return self._registry

    def create(self, name: str, /, **kwargs: Any) -> Reranker:
        resolved = _RERANKER_ALIASES.get(name.lower().strip(), name)
        return self._registry.get(resolved, **kwargs)

    def create_all(self, **kwargs: Any) -> list[Reranker]:
        return self._registry.create_all(**kwargs)

    def available_rerankers(self) -> list[str]:
        return self._registry.list_names()
