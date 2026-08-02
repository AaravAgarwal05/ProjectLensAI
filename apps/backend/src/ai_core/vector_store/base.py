"""Abstract vector-store interface.

Every vector-store provider implements ``VectorStore``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.ai_core.vector_store.models import DeleteResult, VectorDocument, VectorHit


class VectorStore(ABC):
    """Interface for vector database operations.

    Stores, updates, deletes, and retrieves ``VectorDocument`` objects.
    Retrieval methods (``query`` / ``fetch_all``) return raw hits — ranking
    and reranking happen one layer up.
    """

    @property
    @abstractmethod
    def store_name(self) -> str:
        """Human-readable provider identifier."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check whether the store is reachable and operational."""

    # -- Collection lifecycle ------------------------------------------------

    @abstractmethod
    async def create_collection(self, name: str, **kwargs: Any) -> bool:
        """Create a new collection.

        Args:
            name: Collection name.
            **kwargs: Provider-specific collection options.

        Returns:
            True if created, False if already exists.
        """

    @abstractmethod
    async def delete_collection(self, name: str) -> bool:
        """Delete a collection and all its vectors."""

    @abstractmethod
    async def collection_exists(self, name: str) -> bool:
        """Check whether a collection exists."""

    @abstractmethod
    async def list_collections(self) -> list[str]:
        """Return all collection names."""

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @abstractmethod
    async def insert(self, collection: str, documents: list[VectorDocument]) -> int:
        """Insert documents into a collection.

        Returns:
            Number of successfully inserted documents.
        """

    @abstractmethod
    async def update(self, collection: str, documents: list[VectorDocument]) -> int:
        """Update existing documents by chunk_id.

        Returns:
            Number of successfully updated documents.
        """

    @abstractmethod
    async def delete(
        self,
        collection: str,
        chunk_ids: list[str] | None = None,
        filter: dict[str, Any] | None = None,
    ) -> int:
        """Delete documents from a collection.

        Args:
            collection: Collection name.
            chunk_ids: Specific chunk IDs to delete.
            filter: Metadata filter dict.

        Returns:
            Number of deleted documents.
        """

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @abstractmethod
    async def count(self, collection: str) -> int:
        """Return the number of documents in a collection."""

    @abstractmethod
    async def delete_by_report(self, collection: str, report_id: str) -> DeleteResult:
        """Delete all documents for a given report_id."""

    @abstractmethod
    async def delete_by_version(self, collection: str, version_id: str) -> DeleteResult:
        """Delete all documents for a given version_id."""

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    @abstractmethod
    async def query(
        self,
        collection: str,
        embedding: list[float],
        top_k: int = 10,
    ) -> list[VectorHit]:
        """Return the *top_k* nearest vectors to *embedding* in *collection*.

        Hits are ordered most-similar first; ``VectorHit.score`` is a similarity
        score (higher is better). Raises a store error if the collection does
        not exist.
        """

    @abstractmethod
    async def fetch_all(self, collection: str) -> list[VectorHit]:
        """Return every vector in *collection* (used by keyword/BM25 legs).

        ``VectorHit.score`` is 0 for all hits.
        """

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    @abstractmethod
    def configure(self, params: dict[str, Any]) -> None:
        """Reconfigure the store at runtime."""
