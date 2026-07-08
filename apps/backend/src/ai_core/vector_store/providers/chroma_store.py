"""ChromaDB vector-store provider.

Uses the ChromaDB Python client with in-memory or persistent storage.
"""

from __future__ import annotations

import logging
from typing import Any

from src.ai_core.vector_store.base import VectorStore
from src.ai_core.vector_store.models import DeleteResult, VectorDocument

logger = logging.getLogger(__name__)


class ChromaVectorStore(VectorStore):
    """Vector-store provider wrapping ChromaDB.

    Configuration:
        path: Persistence directory (``None`` for in-memory).
        collection_metadata: Extra metadata for new collections.
    """

    def __init__(
        self,
        path: str | None = None,
        collection_metadata: dict[str, Any] | None = None,
    ) -> None:
        self._path = path
        self._collection_metadata = collection_metadata or {}
        self._client: Any = None
        self._collections: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Lazy client
    # ------------------------------------------------------------------

    @property
    def _client(self) -> Any:
        return self.__client

    @_client.setter
    def _client(self, val: Any) -> None:
        self.__client = val

    @property
    def client(self) -> Any:
        """Lazy-initialized ChromaDB client."""
        if self.__client is None:
            import chromadb

            kwargs: dict[str, Any] = {}
            if self._path:
                kwargs["path"] = self._path
            self.__client = chromadb.PersistentClient(**kwargs) if self._path else chromadb.Client()
        return self.__client

    def __init_subclass__(cls, **kwargs: Any) -> None:
        pass

    # ------------------------------------------------------------------
    # VectorStore interface
    # ------------------------------------------------------------------

    @property
    def store_name(self) -> str:
        return "chroma"

    async def health_check(self) -> bool:
        try:
            self.client.heartbeat()
            return True
        except Exception:
            return False

    async def create_collection(self, name: str, **kwargs: Any) -> bool:
        if await self.collection_exists(name):
            return False
        meta = {**self._collection_metadata, **kwargs.get("metadata", {})}
        col = self.client.get_or_create_collection(name=name, metadata=meta or None)
        self._collections[name] = col
        return True

    async def delete_collection(self, name: str) -> bool:
        if not await self.collection_exists(name):
            return False
        try:
            self.client.delete_collection(name)
            self._collections.pop(name, None)
            return True
        except Exception:
            return False

    async def collection_exists(self, name: str) -> bool:
        try:
            self.client.get_collection(name)
            return True
        except Exception:
            return False

    async def list_collections(self) -> list[str]:
        cols = self.client.list_collections()
        return [c.name for c in cols]

    async def insert(self, collection: str, documents: list[VectorDocument]) -> int:
        col = self._get_collection(collection)
        ids = [d.chunk_id for d in documents]
        vectors = [d.vector for d in documents]
        metadatas = [_to_chroma_meta(d) for d in documents]
        col.add(ids=ids, embeddings=vectors, metadatas=metadatas)
        return len(documents)

    async def update(self, collection: str, documents: list[VectorDocument]) -> int:
        col = self._get_collection(collection)
        ids = [d.chunk_id for d in documents]
        vectors = [d.vector for d in documents]
        metadatas = [_to_chroma_meta(d) for d in documents]
        col.update(ids=ids, embeddings=vectors, metadatas=metadatas)
        return len(documents)

    async def delete(
        self,
        collection: str,
        chunk_ids: list[str] | None = None,
        filter: dict[str, Any] | None = None,
    ) -> int:
        col = self._get_collection(collection)
        where = filter or {}
        ids = chunk_ids
        col.delete(ids=ids, where=where or None)
        return len(ids) if ids else 0

    async def count(self, collection: str) -> int:
        col = self._get_collection(collection)
        return col.count()  # type: ignore[no-any-return]

    async def delete_by_report(self, collection: str, report_id: str) -> DeleteResult:
        try:
            col = self._get_collection(collection)
            col.delete(where={"report_id": report_id})
            return DeleteResult(collection_name=collection, deleted_count=-1)
        except Exception as exc:
            return DeleteResult(
                collection_name=collection,
                successful=False,
                errors=[str(exc)],
            )

    async def delete_by_version(self, collection: str, version_id: str) -> DeleteResult:
        try:
            col = self._get_collection(collection)
            col.delete(where={"version_id": version_id})
            return DeleteResult(collection_name=collection, deleted_count=-1)
        except Exception as exc:
            return DeleteResult(
                collection_name=collection,
                successful=False,
                errors=[str(exc)],
            )

    def configure(self, params: dict[str, Any]) -> None:
        if "path" in params:
            self._path = params["path"]
            self.__client = None
            self._collections.clear()
        if "collection_metadata" in params:
            self._collection_metadata.update(params["collection_metadata"])

    def _get_collection(self, name: str) -> Any:
        if name not in self._collections:
            self._collections[name] = self.client.get_collection(name)
        return self._collections[name]


def _to_chroma_meta(doc: VectorDocument) -> dict[str, Any]:
    """Convert VectorDocument metadata to a ChromaDB metadata dict."""
    meta: dict[str, Any] = {
        "chunk_id": doc.chunk_id,
        "report_id": doc.metadata.report_id,
        "version_id": doc.metadata.version_id,
        "embedding_model": doc.metadata.embedding_model,
        "embedding_provider": doc.metadata.embedding_provider,
    }
    if doc.metadata.extra:
        meta.update(doc.metadata.extra)
    return meta
