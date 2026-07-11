"""No-op reranker — passes candidates through unchanged."""

from __future__ import annotations

from typing import Any

from src.ai_core.retrieval.models import RetrievedChunk, SearchQuery
from src.ai_core.retrieval.reranking.base import Reranker


class NoReranker(Reranker):
    """Reranker that returns candidates as-is, without re-scoring.

    Used as the default when no reranking is requested.
    """

    @property
    def reranker_name(self) -> str:
        return "none"

    async def rerank(
        self,
        query: SearchQuery,
        candidates: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        return candidates

    def configure(self, params: dict[str, Any]) -> None:
        pass
