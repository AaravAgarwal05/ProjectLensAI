"""MultiDocumentStrategy — context assembly across multiple documents."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from src.ai_core.context.base import ContextStrategy
from src.ai_core.context.configuration import ContextConfiguration
from src.ai_core.context.models import (
    ContextBudget,
    ContextChunk,
    ContextMetadata,
    ConversationMessage,
    LLMContext,
)

logger = logging.getLogger(__name__)


class MultiDocumentStrategy(ContextStrategy):
    """Assembles context for queries spanning multiple documents."""

    @property
    def strategy_name(self) -> str:
        return "multi_document"

    def __init__(self) -> None:
        self._max_chunks_per_doc = 10

    async def assemble(
        self,
        query: str,
        chunks: list[ContextChunk],
        history: list[ConversationMessage],
        config: ContextConfiguration,
    ) -> LLMContext:
        ctx = LLMContext(query=query)

        doc_chunks = self._group_by_document(chunks)
        ctx.system_prompt = self._build_system_prompt(doc_chunks)

        selected = self._sample_across_docs(doc_chunks)
        ctx.chunks = selected

        ctx.budget = ContextBudget(
            total=config.max_tokens,
            system_prompt=config.system_prompt_tokens,
            retrieved_chunks=sum(c.token_count or len(c.content) // 4 for c in selected),
        )

        ctx.metadata = ContextMetadata(
            query_text=query,
            strategy=self.strategy_name,
            num_chunks=len(selected),
            total_tokens=ctx.budget.allocated,
        )
        ctx.conversation_history = history
        ctx.successful = True
        return ctx

    def _group_by_document(
        self,
        chunks: list[ContextChunk],
    ) -> dict[str, list[ContextChunk]]:
        groups: dict[str, list[ContextChunk]] = defaultdict(list)
        for c in chunks:
            doc_id = c.source_id or c.source_title or "unknown"
            groups[doc_id].append(c)
        for doc_id in groups:
            groups[doc_id].sort(key=lambda x: x.score, reverse=True)
        return dict(groups)

    def _sample_across_docs(
        self,
        doc_chunks: dict[str, list[ContextChunk]],
    ) -> list[ContextChunk]:
        selected: list[ContextChunk] = []
        for doc_chunks_list in doc_chunks.values():
            selected.extend(doc_chunks_list[: self._max_chunks_per_doc])
        return sorted(selected, key=lambda c: c.score, reverse=True)

    def _build_system_prompt(
        self,
        doc_chunks: dict[str, list[ContextChunk]],
    ) -> str:
        doc_names = list(doc_chunks.keys())
        docs = ", ".join(doc_names) if len(doc_names) <= 3 else f"{len(doc_names)} documents"
        return (
            f"You are a helpful multi-document analysis assistant. The user is referencing: {docs}."
        )

    def configure(self, params: dict[str, Any]) -> None:
        if "max_chunks_per_doc" in params:
            self._max_chunks_per_doc = int(params["max_chunks_per_doc"])
