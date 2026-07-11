"""ComparisonStrategy — side-by-side context across documents."""

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


class ComparisonStrategy(ContextStrategy):
    """Assembles context for comparing documents side by side."""

    @property
    def strategy_name(self) -> str:
        return "comparison"

    def __init__(self) -> None:
        self._max_per_source = 8

    async def assemble(
        self,
        query: str,
        chunks: list[ContextChunk],
        history: list[ConversationMessage],
        config: ContextConfiguration,
    ) -> LLMContext:
        ctx = LLMContext(query=query)

        sources = self._group_by_source(chunks)
        ctx.system_prompt = self._build_system_prompt(sources)

        paired = self._pair_chunks(sources)
        ctx.chunks = paired

        ctx.budget = ContextBudget(
            total=config.max_tokens,
            system_prompt=config.system_prompt_tokens,
            retrieved_chunks=sum(c.token_count or len(c.content) // 4 for c in paired),
        )

        ctx.metadata = ContextMetadata(
            query_text=query,
            strategy=self.strategy_name,
            num_chunks=len(paired),
            total_tokens=ctx.budget.allocated,
        )
        ctx.conversation_history = history
        ctx.successful = True
        return ctx

    def _group_by_source(self, chunks: list[ContextChunk]) -> dict[str, list[ContextChunk]]:
        groups: dict[str, list[ContextChunk]] = defaultdict(list)
        for c in chunks:
            src = c.source_id or c.source_title or "unknown"
            groups[src].append(c)
        for src in groups:
            groups[src].sort(key=lambda x: x.score, reverse=True)
        return dict(groups)

    def _pair_chunks(self, sources: dict[str, list[ContextChunk]]) -> list[ContextChunk]:
        paired: list[ContextChunk] = []
        # Interleave chunks from different sources for side-by-side
        source_list = list(sources.values())
        max_per_source = min(
            self._max_per_source,
            max((len(s) for s in source_list), default=0),
        )
        for i in range(max_per_source):
            for src_chunks in source_list:
                if i < len(src_chunks):
                    paired.append(src_chunks[i])
        return paired

    def _build_system_prompt(self, sources: dict[str, list[ContextChunk]]) -> str:
        names = sorted(sources.keys())[:5]
        desc = ", ".join(names)
        return (
            "You are a comparison analysis assistant. "
            f"Compare and contrast the following sources: {desc}."
        )

    def configure(self, params: dict[str, Any]) -> None:
        if "max_per_source" in params:
            self._max_per_source = int(params["max_per_source"])
