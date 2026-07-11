"""Multi-Query retriever — expands a single query into variants, retrieves
each, and merges the results.

Uses simple heuristic expansion (no LLM):
- Original query
- Fewer keywords version
- Synonym-substituted version
- More specific version
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.ai_core.retrieval.base import Retriever
from src.ai_core.retrieval.models import (
    RetrievalResult,
    RetrievedChunk,
    SearchQuery,
)

logger = logging.getLogger(__name__)


class MultiQueryRetriever(Retriever):
    """Retriever that generates multiple query variants and merges results.

    Delegates actual retrieval to a ``base_retriever`` (typically a
    ``DenseRetriever``).  Query expansion is simple text manipulation.

    Configuration keys (via ``configure``):
        top_k: Default top-k (default 10).
        num_variants: Number of query variants (default 3).
        score_threshold: Minimum score (optional).
        collection: Target collection name.
    """

    def __init__(
        self,
        base_retriever: Retriever | None = None,
        top_k: int = 10,
        num_variants: int = 3,
        score_threshold: float | None = None,
        collection: str | None = None,
    ) -> None:
        self._base = base_retriever
        self._top_k = top_k
        self._num_variants = num_variants
        self._score_threshold = score_threshold
        self._collection_name = collection or "default"

    @property
    def retriever_name(self) -> str:
        return "multi_query"

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

        variants = self._expand_query(query.text)
        variants.insert(0, query.text)

        if self._num_variants is not None:
            variants = variants[: self._num_variants]

        all_chunks: list[RetrievedChunk] = []
        for variant in variants:
            vq = SearchQuery(
                text=variant,
                top_k=top_k,
                score_threshold=None,
                include_metadata=query.include_metadata,
                filter=query.filter,
                collection=col,
            )
            if self._base is not None:
                vr = await self._base.retrieve(vq)
                if vr.successful:
                    all_chunks.extend(vr.chunks)

        merged = self._merge_and_dedup(all_chunks)
        merged.sort(key=lambda c: c.score, reverse=True)

        if query.score_threshold is not None:
            merged = [c for c in merged if c.score >= query.score_threshold]

        result.chunks = merged[:top_k]
        result.metadata.num_candidates = len(merged)
        elapsed = time.monotonic() - start
        result.metadata.total_time = elapsed

        return result

    def _expand_query(self, query: str) -> list[str]:
        """Generate query variants via simple heuristics."""
        variants: list[str] = []
        tokens = query.strip().split()
        if not tokens:
            return variants

        # 1. Fewer keywords — drop every other word
        if len(tokens) > 3:
            short = " ".join(tokens[::2])
            variants.append(short)

        # 2. Key terms only — nouns / first and last
        if len(tokens) > 2:
            key = f"{tokens[0]} {tokens[-1]}"
            if key != query.strip():
                variants.append(key)

        # 3. Synonym version — simple word swaps
        synonym_map = {
            "find": "search",
            "get": "retrieve",
            "show": "list",
            "how": "what",
            "document": "file",
            "report": "analysis",
            "create": "make",
            "change": "modify",
            "delete": "remove",
            "error": "issue",
        }
        syn_tokens = [synonym_map.get(t, t) for t in tokens]
        syn_query = " ".join(syn_tokens)
        if syn_query != query.strip():
            variants.append(syn_query)

        return variants

    def _merge_and_dedup(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Merge chunks from multiple queries, deduplicating by chunk_id."""
        seen: dict[str, RetrievedChunk] = {}
        for c in chunks:
            if c.chunk_id in seen:
                existing = seen[c.chunk_id]
                existing.score = max(existing.score, c.score)
                if not existing.content:
                    existing.content = c.content
            else:
                seen[c.chunk_id] = RetrievedChunk(
                    chunk_id=c.chunk_id,
                    content=c.content,
                    score=c.score,
                    metadata=c.metadata,
                    document_id=c.document_id,
                )
        return list(seen.values())

    def configure(self, params: dict[str, Any]) -> None:
        if "top_k" in params:
            self._top_k = int(params["top_k"])
        if "num_variants" in params:
            self._num_variants = int(params["num_variants"])
        if "score_threshold" in params:
            self._score_threshold = params["score_threshold"]
        if "collection" in params:
            self._collection_name = params["collection"]
