"""SingleDocumentStrategy — default strategy for single-document queries."""

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


class SingleDocumentStrategy(ContextStrategy):
    """Assembles context focused on a single document."""

    @property
    def strategy_name(self) -> str:
        return "single_document"

    def __init__(self) -> None:
        self._system_prompt = self._grounding_prompt()

    async def assemble(
        self,
        query: str,
        chunks: list[ContextChunk],
        history: list[ConversationMessage],
        config: ContextConfiguration,
    ) -> LLMContext:
        ctx = LLMContext(query=query)

        ctx.system_prompt = self._build_system_prompt(chunks)
        ctx.chunks = self._rank_and_select(chunks)

        ctx.budget = ContextBudget(
            total=config.max_tokens,
            system_prompt=config.system_prompt_tokens,
            retrieved_chunks=sum(c.token_count or len(c.content) // 4 for c in ctx.chunks),
        )

        ctx.metadata = ContextMetadata(
            query_text=query,
            strategy=self.strategy_name,
            num_chunks=len(ctx.chunks),
            total_tokens=ctx.budget.allocated,
        )

        ctx.conversation_history = history
        ctx.successful = bool(ctx.chunks) or bool(query)
        return ctx

    @staticmethod
    def _grounding_prompt() -> str:
        """Strict grounding instructions — answer only from the retrieved context."""
        return (
            "You are a document analysis assistant. Answer STRICTLY from the retrieved context.\n"
            "Rules:\n"
            "1. Base every claim on the retrieved context. Never use outside knowledge.\n"
            "2. Use the context to answer: extract the relevant facts, and aggregate or "
            "compare across chunks when the question asks for it (e.g. highest/lowest, "
            "totals, distributions).\n"
            "3. For each fact you state, cite the chunk it came from as [Chunk N].\n"
            "4. Do not add general knowledge, extra examples, or elaborations "
            "not present in the context.\n"
            "5. Only if the context genuinely has none of the information needed, "
            "answer exactly: \"The retrieved context doesn't cover this question.\"\n"
            "6. If only part of the answer is in the context, answer that part "
            "and note the rest is not covered."
        )

    def _build_system_prompt(self, chunks: list[ContextChunk]) -> str:
        titles = {c.source_title for c in chunks if c.source_title}
        base = self._grounding_prompt()
        if titles:
            docs = ", ".join(sorted(titles))
            return f"{base}\nThe user is asking about: {docs}."
        return base

    def _rank_and_select(self, chunks: list[ContextChunk]) -> list[ContextChunk]:
        return sorted(chunks, key=lambda c: c.score, reverse=True)[:20]

    def configure(self, params: dict[str, Any]) -> None:
        if "system_prompt" in params:
            self._system_prompt = str(params["system_prompt"])
