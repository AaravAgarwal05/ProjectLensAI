"""Abstract retriever interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RetrievedChunk:
    """A chunk returned by a retriever, with a relevance score."""

    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    document_id: str | None = None


class BaseRetriever(ABC):
    """Interface for retrieval strategies.

    Subclasses implement different backends: vector similarity search,
    full-text search, hybrid, or re-ranking pipelines.
    """

    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
        """Retrieve the most relevant chunks for a query.

        Args:
            query: The search query.
            top_k: Maximum number of chunks to return.

        Returns:
            A list of retrieved chunks sorted by relevance (best first).
        """

    @abstractmethod
    async def retrieve_with_scores(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[tuple[RetrievedChunk, float]]:
        """Retrieve chunks together with their raw similarity scores.

        Args:
            query: The search query.
            top_k: Maximum number of chunks to return.

        Returns:
            A list of ``(chunk, score)`` tuples, sorted by score descending.
        """
