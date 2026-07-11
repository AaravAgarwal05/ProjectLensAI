"""Abstract reranker interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.ai_core.retrieval.models import RetrievedChunk, SearchQuery


class Reranker(ABC):
    """Interface for reranking strategies.

    Rerankers re-score a list of candidate chunks given the original query.
    """

    @property
    @abstractmethod
    def reranker_name(self) -> str:
        """Human-readable provider identifier."""

    @abstractmethod
    async def rerank(
        self,
        query: SearchQuery,
        candidates: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """Re-rank candidate chunks and return them sorted by new score."""

    @abstractmethod
    def configure(self, params: dict[str, Any]) -> None:
        """Reconfigure the reranker at runtime."""
