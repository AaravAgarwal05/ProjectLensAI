"""Retrieval pipeline — orchestrates the query-to-results lifecycle.

Pipeline:
    Query → Retriever → Reranker → Validation → Results

Supports hooks: before_retrieval, after_retrieval, before_reranking, after_reranking.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.ai_core.retrieval.base import Retriever
from src.ai_core.retrieval.configuration import RetrieverConfiguration
from src.ai_core.retrieval.exceptions import RetrievalError
from src.ai_core.retrieval.hooks import RetrievalHookRegistry
from src.ai_core.retrieval.models import RetrievalResult, SearchQuery
from src.ai_core.retrieval.reranking.base import Reranker
from src.ai_core.retrieval.validation import RetrievalValidationEngine

logger = logging.getLogger(__name__)


class RetrievalPipeline:
    """Orchestrates the full retrieval lifecycle.

    Typical usage::

        pipeline = RetrievalPipeline(retriever=store, reranker=reranker)
        result = await pipeline.run(query)
    """

    def __init__(
        self,
        retriever: Retriever,
        reranker: Reranker | None = None,
        config: RetrieverConfiguration | None = None,
        validation: RetrievalValidationEngine | None = None,
        hooks: RetrievalHookRegistry | None = None,
    ) -> None:
        self._retriever = retriever
        self._reranker = reranker
        self._config = config or RetrieverConfiguration.default()
        self._validation = validation or RetrievalValidationEngine()
        self._hooks = hooks or RetrievalHookRegistry()

    @property
    def retriever(self) -> Retriever:
        return self._retriever

    @property
    def reranker(self) -> Reranker | None:
        return self._reranker

    @property
    def hooks(self) -> RetrievalHookRegistry:
        return self._hooks

    async def run(
        self,
        query: SearchQuery,
    ) -> RetrievalResult:
        """Run the full retrieval pipeline.

        Args:
            query: The search query.

        Returns:
            A ``RetrievalResult``.
        """
        start = time.monotonic()
        result = RetrievalResult(query=query)
        result.metadata.retriever_name = self._retriever.retriever_name
        result.metadata.reranker_name = self._reranker.reranker_name if self._reranker else "none"
        result.metadata.query_text = query.text

        if not query.text.strip():
            result.errors.append("Empty query text")
            result.successful = False
            return result

        # Before retrieval hook
        query = await self._hooks.run_before_retrieval(query)

        # Retrieve
        try:
            retrieval = await self._retriever.retrieve(query)
        except RetrievalError as exc:
            result.errors.append(f"Retrieval failed: {exc}")
            result.successful = False
            return result
        except Exception as exc:
            result.errors.append(f"Unexpected retrieval error: {exc}")
            result.successful = False
            return result

        chunks = retrieval.chunks

        # After retrieval hook
        chunks = await self._hooks.run_after_retrieval(chunks)

        # Before reranking hook
        chunks = await self._hooks.run_before_reranking(chunks)

        # Rerank
        if self._reranker is not None and chunks:
            try:
                chunks = await self._reranker.rerank(query, chunks)
            except Exception as exc:
                result.warnings.append(f"Reranking failed (continuing with candidates): {exc}")

        result.chunks = chunks

        # After reranking hook
        result = await self._hooks.run_after_reranking(result)

        # Validation
        vr = self._validation.validate_result(result)
        if vr.errors:
            result.errors.extend(vr.errors)
            result.successful = False
        for w in vr.warnings:
            if w not in result.warnings:
                result.warnings.append(w)

        # Metadata
        elapsed = time.monotonic() - start
        result.metadata.total_time = elapsed
        result.metadata.num_candidates = len(chunks)

        return result

    def configure(self, params: dict[str, Any]) -> None:
        """Reconfigure pipeline components."""
        if self._reranker is not None and "reranker" in params:
            self._reranker.configure(params["reranker"])
        if "retriever" in params:
            self._retriever.configure(params["retriever"])
