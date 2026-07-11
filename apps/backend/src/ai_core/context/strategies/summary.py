"""SummaryStrategy — condensed context for summarization queries."""

from __future__ import annotations

import logging
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


class SummaryStrategy(ContextStrategy):
    """Assembles a condensed context for summarization tasks."""

    @property
    def strategy_name(self) -> str:
        return "summary"

    def __init__(self) -> None:
        self._max_summary_chunks = 5

    async def assemble(
        self,
        query: str,
        chunks: list[ContextChunk],
        history: list[ConversationMessage],
        config: ContextConfiguration,
    ) -> LLMContext:
        ctx = LLMContext(query=query)

        ctx.system_prompt = (
            "You are a summarization assistant. "
            "Provide a concise summary of the provided content."
        )

        top_chunks = self._select_top_chunks(chunks)
        condensed = self._condense(top_chunks)
        ctx.chunks = condensed

        ctx.budget = ContextBudget(
            total=config.max_tokens,
            system_prompt=config.system_prompt_tokens,
            retrieved_chunks=sum(c.token_count or len(c.content) // 4 for c in condensed),
        )

        ctx.metadata = ContextMetadata(
            query_text=query,
            strategy=self.strategy_name,
            num_chunks=len(condensed),
            total_tokens=ctx.budget.allocated,
        )
        ctx.conversation_history = history
        ctx.successful = True
        return ctx

    def _select_top_chunks(self, chunks: list[ContextChunk]) -> list[ContextChunk]:
        return sorted(chunks, key=lambda c: c.score, reverse=True)[: self._max_summary_chunks]

    def _condense(self, chunks: list[ContextChunk]) -> list[ContextChunk]:
        """Merge all chunks into a single condensed chunk."""
        if not chunks:
            return chunks

        combined = "\n\n".join(c.content for c in chunks)
        token_count = len(combined) // 4
        return [
            ContextChunk(
                chunk_id="summary_combined",
                content=combined,
                score=max(c.score for c in chunks),
                citations=list({cite for c in chunks for cite in c.citations}),
                token_count=token_count,
            )
        ]

    def configure(self, params: dict[str, Any]) -> None:
        if "max_summary_chunks" in params:
            self._max_summary_chunks = int(params["max_summary_chunks"])
