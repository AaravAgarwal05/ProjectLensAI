"""Token budget enforcement and context truncation for chat.

Provides a TokenBudget class and helper functions to truncate
conversation history and retrieved context chunks so the combined
payload fits within the LLM's context window.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.ai_core.context.models import ContextChunk
from src.ai_core.tokenizer import estimate_tokens as _estimate_tokens

logger = logging.getLogger(__name__)


@dataclass
class TokenBudget:
    """Allocation of the available context window.

    ``max_context_tokens`` is the total LLM context window.
    ``response_tokens`` is reserved for the generation output.
    Remaining tokens are split between system prompt, history, and chunks.
    """

    max_context_tokens: int = 4096
    response_tokens: int = 1024
    system_prompt_tokens: int = 500

    # ------------------------------------------------------------------
    # Derived
    # ------------------------------------------------------------------

    @property
    def available_tokens(self) -> int:
        """Tokens remaining for history + chunks."""
        return self.max_context_tokens - self.response_tokens - self.system_prompt_tokens

    @property
    def history_budget(self) -> int:
        """Max tokens for conversation history (half of available)."""
        return max(256, self.available_tokens // 2)

    @property
    def chunks_budget(self) -> int:
        """Max tokens for retrieved chunks (half of available)."""
        return max(256, self.available_tokens // 2)


def truncate_chunks(
    chunks: list[ContextChunk],
    budget: TokenBudget | None = None,
) -> list[ContextChunk]:
    """Sort chunks by score descending, drop low-score ones, truncate content.

    Args:
        chunks: Retrieved context chunks.
        budget: Token budget to enforce.

    Returns:
        Filtered / truncated chunks list.
    """
    b = budget or TokenBudget()
    limit = b.chunks_budget

    if not chunks:
        return []

    # Sort by score descending
    sorted_chunks = sorted(chunks, key=lambda c: c.score, reverse=True)

    kept: list[ContextChunk] = []
    used = 0

    for chunk in sorted_chunks:
        tokens = _estimate_tokens(chunk.content)

        # If this single chunk is too large, truncate its content
        if used + tokens > limit:
            allowed_chars = (limit - used) * 4
            if allowed_chars > 80 and chunk.content:
                truncated = chunk.content[:allowed_chars]
                kept.append(
                    ContextChunk(
                        chunk_id=chunk.chunk_id,
                        content=truncated,
                        score=chunk.score,
                        source_id=chunk.source_id,
                        source_title=chunk.source_title,
                        page_number=chunk.page_number,
                        section_name=chunk.section_name,
                        token_count=_estimate_tokens(truncated),
                        metadata=chunk.metadata,
                    )
                )
                used += _estimate_tokens(truncated)
            break

        kept.append(chunk)
        used += tokens

    logger.debug(
        "truncate_chunks: kept %d / %d chunks (%d tokens of %d budget)",
        len(kept),
        len(chunks),
        used,
        limit,
    )
    return kept
