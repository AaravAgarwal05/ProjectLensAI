"""Hybrid retriever — combines dense vector search with keyword search.

Uses weighted scoring, duplicate merging, and score normalisation.
Keyword search is a simple term-frequency fallback (BM25-like via
in-memory term counting) when no external full-text engine is available.
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
        tokens = query.text.lower().split()
        term_counts: Counter[str] = Counter(tokens)
        total_terms = sum(term_counts.values())
        if total_terms == 0:
            return []

        # If we have a chroma collection, pull all documents for keyword scoring
        # Otherwise build scored chunks from the dense result metadata
        chunks: list[RetrievedChunk] = []
        if self._chroma_collection is not None:
            try:
                all_data = self._chroma_collection.get()
                all_ids = all_data.get("ids", [])
                all_docs = all_data.get("documents", [])
                all_metas = all_data.get("metadatas", [])
                for i in range(len(all_ids)):
                    doc_text = (all_docs[i] or "").lower()
                    score = self._tf_score(doc_text, term_counts, total_terms)
                    meta = all_metas[i] if all_metas else {}
                    chunks.append(
                        RetrievedChunk(
                            chunk_id=all_ids[i],
                            content=all_docs[i] or "",
                            score=score,
                            metadata=meta,
                            document_id=meta.get("report_id") or meta.get("document_id"),
                        )
                    )
            except Exception:
                logger.debug("Sparse fallback: chroma.get() failed, using empty")
        return chunks

    def _tf_score(self, text: str, term_counts: Counter[str], total_terms: int) -> float:
        """Simple TF-based relevance score."""
        if total_terms == 0:
            return 0.0
        text_tokens = text.split()
        text_len = len(text_tokens)
        if text_len == 0:
            return 0.0
        score = 0.0
        for term, count in term_counts.items():
            tf = text_tokens.count(term) / text_len
            count_t = text_tokens.count(term)
            idf = math.log((len(text_tokens) + 1) / (1 + count_t)) if count_t > 0 else 0
            score += (tf * idf) * count
        return score / total_terms

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
        if "top_k" in params:
            self._top_k = int(params["top_k"])
        if "score_threshold" in params:
            self._score_threshold = params["score_threshold"]
        if "collection" in params:
            self._collection_name = params["collection"]
