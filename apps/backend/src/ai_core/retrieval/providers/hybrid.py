"""Hybrid retriever — combines dense vector search with keyword search.

Uses weighted scoring, duplicate merging, and score normalisation.
Sparse leg uses BM25Okapi for proper keyword scoring.
"""

from __future__ import annotations

import logging
import math
import time
from collections import Counter
from typing import Any

from src.ai_core.retrieval.base import Retriever
from src.ai_core.retrieval.models import (
    RetrievalResult,
    RetrievedChunk,
    SearchQuery,
)

logger = logging.getLogger(__name__)


# ── inline BM25Okapi ─────────────────────────────────────────────────────────


class _BM25Okapi:
    """BM25Okapi scoring — built lazily from a list of documents.

    Parameters
    ----------
    k1 : float
        Term-frequency saturation (default 1.2).
    b : float
        Length normalisation (default 0.75).
    """

    def __init__(self, k1: float = 1.2, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._docs: list[str] = []
        self._doc_lens: list[int] = []
        self._avgdl: float = 0.0
        self._n_docs: int = 0
        self._df: Counter[str] = Counter()  # document frequency per term
        self._built: bool = False

    def build(self, docs: list[str]) -> None:
        """Pre-compute document lengths and term document frequencies."""
        self._docs = docs
        self._doc_lens = [len(d.split()) for d in docs]
        self._n_docs = len(docs)
        self._avgdl = sum(self._doc_lens) / self._n_docs if self._n_docs else 0.0

        # Count how many docs each term appears in
        self._df.clear()
        for doc in docs:
            seen = set(doc.lower().split())
            for term in seen:
                self._df[term] += 1

        self._built = True

    def score(self, query: str, doc_idx: int) -> float:
        """BM25 score for *query* against document at *doc_idx*."""
        if not self._built or doc_idx >= self._n_docs:
            return 0.0

        query_terms = query.lower().split()
        doc = self._docs[doc_idx].lower()
        doc_len = self._doc_lens[doc_idx]
        doc_tokens = doc.split()
        doc_tf = Counter(doc_tokens)

        total = 0.0
        for term in set(query_terms):
            tf = doc_tf.get(term, 0)
            if tf == 0:
                continue
            df = self._df.get(term, 1)
            # IDF with smoothing
            idf = math.log((self._n_docs - df + 0.5) / (df + 0.5) + 1.0)
            # TF saturation
            tf_norm = tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * doc_len / self._avgdl))
            total += idf * tf_norm

        return total

    def score_all(self, query: str) -> list[float]:
        """Score *query* against every document in the index."""
        return [self.score(query, i) for i in range(self._n_docs)]


class HybridRetriever(Retriever):
    """Retriever that fuses dense and sparse signals.

    Expects a ``dense_retriever`` that returns scored results.
    Falls back to a simple TF-based keyword scorer for the sparse leg.

    Configuration keys (via ``configure``):
        weights: ``{"dense": 0.5, "sparse": 0.5}``
        top_k: Default top-k (default 10).
        score_threshold: Minimum combined score (optional).
        collection: Target collection name.
    """

    def __init__(
        self,
        dense_retriever: Retriever | None = None,
        weights: dict[str, float] | None = None,
        top_k: int = 10,
        score_threshold: float | None = None,
        collection: str | None = None,
        chroma_collection: Any = None,
    ) -> None:
        self._dense = dense_retriever
        self._weights = weights or {"dense": 0.5, "sparse": 0.5}
        self._top_k = top_k
        self._score_threshold = score_threshold
        self._collection_name = collection or "default"
        self._chroma_collection = chroma_collection
        # Lazily-built BM25 index
        self._bm25 = _BM25Okapi()
        self._bm25_doc_version: int = 0
        self._bm25_n_docs: int = 0

    @property
    def retriever_name(self) -> str:
        return "hybrid"

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
        top_k = query.top_k or self._top_k

        # Dense leg
        dense_result = await self._run_dense(query, col, top_k)
        dense_chunks: list[RetrievedChunk] = dense_result.chunks if dense_result.successful else []

        # Sparse leg
        sparse_chunks = await self._run_sparse(query, col, top_k)

        # Normalise scores to [0, 1]
        self._normalise_scores(dense_chunks)
        self._normalise_scores(sparse_chunks)

        # Merge with weighted scoring
        merged = self._merge_weighted(dense_chunks, sparse_chunks)

        # Sort and trim
        merged.sort(key=lambda c: c.score, reverse=True)
        if query.score_threshold is not None:
            merged = [c for c in merged if c.score >= query.score_threshold]
        merged = merged[:top_k]

        result.chunks = merged
        result.metadata.num_candidates = len(merged)
        elapsed = time.monotonic() - start
        result.metadata.total_time = elapsed

        return result

    async def _run_dense(
        self,
        query: SearchQuery,
        collection: str,
        top_k: int,
    ) -> RetrievalResult:
        q = SearchQuery(
            text=query.text,
            top_k=top_k * 2,
            score_threshold=None,
            include_metadata=query.include_metadata,
            filter=query.filter,
            collection=collection,
        )
        if self._dense is not None:
            return await self._dense.retrieve(q)
        return RetrievalResult(query=q, successful=True)

    async def _run_sparse(
        self,
        query: SearchQuery,
        collection: str,
        top_k: int,
    ) -> list[RetrievedChunk]:
        query_text = query.text.strip()
        if not query_text:
            return []

        chunks: list[RetrievedChunk] = []
        if self._chroma_collection is not None:
            try:
                all_data = self._chroma_collection.get()
                all_ids = all_data.get("ids", [])
                all_docs = all_data.get("documents", [])
                all_metas = all_data.get("metadatas", [])

                if not all_ids:
                    return []

                # Rebuild BM25 index if document set changed
                if len(all_ids) != self._bm25_n_docs:
                    self._bm25.build(all_docs)
                    self._bm25_n_docs = len(all_ids)
                    self._bm25_doc_version += 1

                scores = self._bm25.score_all(query_text)
                for i in range(len(all_ids)):
                    meta = all_metas[i] if all_metas else {}
                    chunks.append(
                        RetrievedChunk(
                            chunk_id=all_ids[i],
                            content=all_docs[i] or "",
                            score=scores[i],
                            metadata=meta,
                            document_id=meta.get("report_id") or meta.get("document_id"),
                        )
                    )
            except Exception:
                logger.debug("Sparse fallback: chroma.get() or BM25 failed, using empty")
        return chunks

    def _normalise_scores(self, chunks: list[RetrievedChunk]) -> None:
        if not chunks:
            return
        scores = [c.score for c in chunks]
        min_s, max_s = min(scores), max(scores)
        if max_s - min_s < 1e-9:
            for c in chunks:
                c.score = 1.0
            return
        for c in chunks:
            c.score = (c.score - min_s) / (max_s - min_s)

    def _merge_weighted(
        self,
        dense: list[RetrievedChunk],
        sparse: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        w_dense = self._weights.get("dense", 0.5)
        w_sparse = self._weights.get("sparse", 0.5)

        chunk_map: dict[str, RetrievedChunk] = {}
        for c in dense:
            chunk_map[c.chunk_id] = RetrievedChunk(
                chunk_id=c.chunk_id,
                content=c.content,
                score=c.score * w_dense,
                metadata=c.metadata,
                document_id=c.document_id,
            )
        for c in sparse:
            if c.chunk_id in chunk_map:
                chunk_map[c.chunk_id].score += c.score * w_sparse
            else:
                chunk_map[c.chunk_id] = RetrievedChunk(
                    chunk_id=c.chunk_id,
                    content=c.content,
                    score=c.score * w_sparse,
                    metadata=c.metadata,
                    document_id=c.document_id,
                )

        return list(chunk_map.values())

    def configure(self, params: dict[str, Any]) -> None:
        if "weights" in params:
            self._weights.update(params["weights"])
            total = sum(self._weights.values())
            if abs(total - 1.0) > 1e-6:
                self._weights = {k: v / total for k, v in self._weights.items()}
        if "top_k" in params:
            self._top_k = int(params["top_k"])
        if "score_threshold" in params:
            self._score_threshold = params["score_threshold"]
        if "collection" in params:
            self._collection_name = params["collection"]
