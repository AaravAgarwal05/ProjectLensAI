"""Token budget manager — allocates and enforces context window."""

from __future__ import annotations

import logging
from typing import Any

from src.ai_core.context.configuration import ContextConfiguration
from src.ai_core.context.models import ContextBudget, ContextChunk, ConversationMessage

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """Rough token estimation (4 chars per token)."""
    return len(text) // 4


class TokenBudgetManager:
    """Allocates token budget across context sections."""

    def __init__(self, config: ContextConfiguration | None = None) -> None:
        self._config = config or ContextConfiguration.default()

    @property
    def config(self) -> ContextConfiguration:
        return self._config

    def configure(self, params: dict[str, Any]) -> None:
        self._config = self._config.merge(params)

    def allocate(
        self,
        query: str,
        chunks: list[ContextChunk],
        history: list[ConversationMessage],
    ) -> ContextBudget:
        """Build a ContextBudget allocating tokens to each section."""
        budget = ContextBudget(total=self._config.max_tokens)

        budget.system_prompt = self._config.system_prompt_tokens
        budget.reserved = self._config.reserved_tokens
        budget.user_query = estimate_tokens(query)

        available = budget.total - budget.system_prompt - budget.reserved - budget.user_query

        history_tokens = sum(estimate_tokens(m.content) for m in history)
        budget.conversation_history = min(history_tokens, self._config.max_history_tokens)

        available -= budget.conversation_history

        chunk_tokens = sum(estimate_tokens(c.content) for c in chunks)
        budget.retrieved_chunks = min(chunk_tokens, self._config.max_chunk_tokens)

        budget.metadata = max(0, available - budget.retrieved_chunks)

        return budget

    def enforce(self, budget: ContextBudget, chunks: list[ContextChunk]) -> list[ContextChunk]:
        """Trim chunks to fit in the retrieved_chunks budget."""
        if not chunks:
            return chunks

        if budget.remaining < 0:
            logger.warning(
                "Token budget exceeded by %d tokens, trimming chunks",
                -budget.remaining,
            )

        fitted: list[ContextChunk] = []
        tokens_used = 0
        max_tokens = budget.retrieved_chunks

        for chunk in chunks:
            chunk_tokens = chunk.token_count or estimate_tokens(chunk.content)
            if tokens_used + chunk_tokens <= max_tokens:
                fitted.append(chunk)
                tokens_used += chunk_tokens
            else:
                # Partial inclusion for last chunk if possible
                remaining = max_tokens - tokens_used
                if remaining > 64 and chunk_tokens > remaining:
                    ratio = remaining / chunk_tokens
                    char_limit = int(len(chunk.content) * ratio)
                    truncated = ChunkProxy(content=chunk.content[:char_limit])
                    fitted.append(
                        ContextChunk(
                            chunk_id=chunk.chunk_id,
                            content=truncated.content,
                            score=chunk.score,
                            source_id=chunk.source_id,
                            source_title=chunk.source_title,
                            token_count=remaining,
                            citations=chunk.citations,
                        )
                    )
                break

        return fitted


class ChunkProxy:
    """Minimal wrapper for truncated content tracking."""

    def __init__(self, content: str) -> None:
        self.content = content
