"""Dense retriever — vector similarity search.

Flow:
    Query → EmbeddingProvider → VectorStore similarity search → Top-K chunks

Configurable: top_k, score_threshold, include_metadata.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.ai_core.embedding.base import EmbeddingProvider
from src.ai_core.retrieval.base import Retriever
from src.ai_core.retrieval.exceptions import EmbeddingError, SearchError
from src.ai_core.retrieval.models import (
    RetrievalResult,
    RetrievedChunk,
    SearchQuery,
)

logger = logging.getLogger(__name__)


class DenseRetriever(Retriever):
    """Retriever that uses dense vector similarity search.

    Requires an ``EmbeddingProvider`` for query encoding and a
    ``collection`` name.  The underlying vector DB is reached via
    a ``_search_fn`` — by default this is a ChromaDB collection's
    ``query`` method.

    Configuration keys (via ``configure``):
        top_k: Default top-k (default 10).
        score_threshold: Minimum similarity score (optional).
        include_metadata: Include metadata (default True).
        collection: Target collection name.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider | None = None,
        collection: str | None = None,
        chroma_collection: Any = None,
        top_k: int = 10,
        score_threshold: float | None = None,
        include_metadata: bool = True,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._collection_name = collection or "default"
        self._chroma_collection = chroma_collection
        self._top_k = top_k
        self._score_threshold = score_threshold
        self._include_metadata = include_metadata

    @property
    def retriever_name(self) -> str:
        return "dense"

    async def retrieve(self, query: SearchQuery) -> RetrievalResult:
        start = time.monotonic()
        result = RetrievalResult(query=query)
        result.metadata.retriever_name = self.retriever_name
        result.metadata.query_text = query.text

        if not query.text.strip():
            result.errors.append("Empty query text")
            result.successful = False
            return result

        col = query.collection or self._collection_name
        result.metadata.collection = col

        top_k = query.top_k or self._top_k

        try:
            query_vec = await self._embed_query(query.text)
        except Exception as exc:
            result.errors.append(f"Embedding failed: {exc}")
            result.successful = False
            return result

        try:
            raw = await self._execute_search(query_vec, col, top_k)
        except Exception as exc:
            result.errors.append(f"Search failed: {exc}")
            result.successful = False
            return result

        chunks = self._parse_search_results(raw, query)

        if query.score_threshold is not None:
            chunks = [c for c in chunks if c.score >= query.score_threshold]

        result.chunks = chunks
        result.metadata.num_candidates = len(chunks)
        elapsed = time.monotonic() - start
        result.metadata.total_time = elapsed

        return result

    async def _embed_query(self, text: str) -> list[float]:
        if self._embedding_provider is None:
            raise EmbeddingError("No embedding provider configured")
        return await self._embedding_provider.embed(text)

    async def _execute_search(
        self,
        query_vec: list[float],
        collection: str,
        top_k: int,
    ) -> Any:
        if self._chroma_collection is None:
            raise SearchError("No vector collection configured for search")
        kwargs: dict[str, Any] = {
            "query_embeddings": [query_vec],
            "n_results": top_k,
        }
        if self._include_metadata:
            kwargs["include"] = ["metadatas", "distances", "documents"]
        return self._chroma_collection.query(**kwargs)

    def _parse_search_results(
        self,
        raw: Any,
        query: SearchQuery,
    ) -> list[RetrievedChunk]:
        chunks: list[RetrievedChunk] = []
        try:
            ids = raw.get("ids", [[]])[0]
            distances = raw.get("distances", [[]])[0]
            documents = raw.get("documents", [[]])[0]
            metadatas = raw.get("metadatas", [[]])[0]
        except (IndexError, TypeError, AttributeError):
            return chunks

        for i in range(len(ids)):
            score = 1.0 - distances[i] if distances else 0.0
            meta = metadatas[i] if metadatas else {}
            chunk = RetrievedChunk(
                chunk_id=ids[i],
                content=documents[i] if documents else "",
                score=score,
                metadata=meta if query.include_metadata else {},
                document_id=meta.get("report_id") or meta.get("document_id"),
            )
            chunks.append(chunk)

        chunks.sort(key=lambda c: c.score, reverse=True)
        return chunks

    def configure(self, params: dict[str, Any]) -> None:
        if "top_k" in params:
            self._top_k = int(params["top_k"])
        if "score_threshold" in params:
            self._score_threshold = params["score_threshold"]
        if "include_metadata" in params:
            self._include_metadata = bool(params["include_metadata"])
        if "collection" in params:
            self._collection_name = params["collection"]
