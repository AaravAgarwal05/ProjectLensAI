"""Context assembly pipeline — orchestrates the full assembly lifecycle.

Pipeline:
    Query + Chunks + History
    → Hooks (before_context)
    → Strategy (assemble)
    → Chunk Selection
    → Metadata Enrichment
    → Conversation Manager
    → Hooks (before_budget)
    → Token Budget (allocate + enforce)
    → Hooks (after_budget)
    → Hooks (after_context)
    → Validation
    → LLMContext
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.ai_core.context.base import ContextStrategy
from src.ai_core.context.budget import TokenBudgetManager
from src.ai_core.context.chunk_selection import ChunkSelectionStrategy
from src.ai_core.context.configuration import ContextConfiguration
from src.ai_core.context.conversation import ConversationManager
from src.ai_core.context.hooks import ContextHookRegistry
from src.ai_core.context.metadata import MetadataEnricher
from src.ai_core.context.models import (
    ContextChunk,
    ConversationMessage,
    LLMContext,
)
from src.ai_core.context.validation import ContextValidationEngine

logger = logging.getLogger(__name__)


class ContextAssemblyPipeline:
    """Orchestrates the full context assembly lifecycle."""

    def __init__(
        self,
        strategy: ContextStrategy,
        config: ContextConfiguration | None = None,
        chunk_selector: ChunkSelectionStrategy | None = None,
        metadata_enricher: MetadataEnricher | None = None,
        conversation_manager: ConversationManager | None = None,
        budget_manager: TokenBudgetManager | None = None,
        validation: ContextValidationEngine | None = None,
        hooks: ContextHookRegistry | None = None,
    ) -> None:
        self._strategy = strategy
        self._config = config or ContextConfiguration.default()
        self._chunk_selector = chunk_selector or ChunkSelectionStrategy(self._config)
        self._metadata_enricher = metadata_enricher or MetadataEnricher()
        self._conversation_manager = conversation_manager or ConversationManager(self._config)
        self._budget_manager = budget_manager or TokenBudgetManager(self._config)
        self._validation = validation or ContextValidationEngine()
        self._hooks = hooks or ContextHookRegistry()

    @property
    def strategy(self) -> ContextStrategy:
        return self._strategy

    @property
    def hooks(self) -> ContextHookRegistry:
        return self._hooks

    async def run(
        self,
        query: str,
        chunks: list[ContextChunk],
        history: list[ConversationMessage] | None = None,
        config: ContextConfiguration | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> LLMContext:
        """Run the full assembly pipeline."""
        start = time.monotonic()
        cfg = config or self._config
        history = history or []

        # Sync sub-managers with active config
        if config is not None:
            self._chunk_selector.configure(cfg.to_dict())
            self._conversation_manager.configure(cfg.to_dict())
            self._budget_manager.configure(cfg.to_dict())

        # Before context hook
        query, chunks, history = await self._hooks.run_before_context(query, chunks, history)

        # Chunk selection
        chunks = self._chunk_selector.select(chunks)

        # Metadata enrichment
        chunks = self._metadata_enricher.enrich(chunks, extra_metadata)

        # Conversation management
        history, summary = self._conversation_manager.prepare(history)

        # Strategy assembly
        ctx = await self._strategy.assemble(query, chunks, history, cfg)

        ctx.conversation_summary = summary
        ctx.metadata.query_text = query
        ctx.metadata.strategy = self._strategy.strategy_name
        ctx.metadata.num_chunks = len(ctx.chunks)
        ctx.metadata.num_messages = len(history)

        # Before budget hook
        ctx = await self._hooks.run_before_budget(ctx)

        # Budget allocation
        budget = self._budget_manager.allocate(query, ctx.chunks, history)
        ctx.budget = budget

        # Enforce budget on chunks
        ctx.chunks = self._budget_manager.enforce(budget, ctx.chunks)

        # After budget hook
        ctx = await self._hooks.run_after_budget(ctx)

        # After context hook
        ctx = await self._hooks.run_after_context(ctx)

        # Statistics
        elapsed = time.monotonic() - start
        ctx.metadata.assembly_time = elapsed
        ctx.metadata.total_tokens = ctx.budget.allocated
        ctx.statistics.context_size = len(ctx.chunks)
        ctx.statistics.token_usage = ctx.budget.allocated
        ctx.statistics.assembly_latency = elapsed
        ctx.statistics.history_utilization = (
            len(history) / cfg.conversation_max_messages
            if cfg.conversation_max_messages > 0
            else 0.0
        )
        ctx.statistics.retrieval_utilization = (
            len(ctx.chunks) / cfg.max_chunks if cfg.max_chunks > 0 else 0.0
        )

        # Validation
        vr = self._validation.validate(ctx)
        if vr.errors:
            ctx.errors.extend(vr.errors)
            ctx.successful = False
        ctx.warnings.extend(w for w in vr.warnings if w not in ctx.warnings)

        return ctx

    def configure(self, params: dict[str, Any]) -> None:
        """Reconfigure pipeline components."""
        if "strategy" in params:
            self._strategy.configure(params["strategy"])
        if "chunk_selector" in params:
            self._chunk_selector.configure(params["chunk_selector"])
        if "conversation" in params:
            self._conversation_manager.configure(params["conversation"])
        if "budget" in params:
            self._budget_manager.configure(params["budget"])
