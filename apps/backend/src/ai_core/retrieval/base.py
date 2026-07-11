"""Abstract retriever interface and base classes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.ai_core.retrieval.models import RetrievalResult, SearchQuery


class Retriever(ABC):
    """Interface for retrieval strategies.

    Subclasses implement different backends: dense vector search,
    hybrid search, multi-query expansion, etc.
    """

    @property
    @abstractmethod
    def retriever_name(self) -> str:
        """Human-readable provider identifier."""

    @abstractmethod
    async def retrieve(
        self,
        query: SearchQuery,
    ) -> RetrievalResult:
        """Retrieve the most relevant chunks for a query.

        Args:
            query: The search query parameters.

        Returns:
            A ``RetrievalResult`` with chunks sorted by relevance.
        """

    @abstractmethod
    def configure(self, params: dict[str, Any]) -> None:
        """Reconfigure the retriever at runtime."""
