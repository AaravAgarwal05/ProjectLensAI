"""Context builder — assembles retrieved chunks into a single context string."""

import logging

from shared.models.document import DocumentChunk

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Builds a consolidated context string from retrieved chunks.

    The builder truncates or prioritises chunks to fit within a token
    budget so that the final context string can be passed directly
    into an LLM prompt.
    """

    def __init__(self) -> None:
        self._token_estimate_factor: float = 4.0  # ~4 chars per token

    def _estimate_tokens(self, text: str) -> int:
        """Rough token count (characters / 4)."""
        return int(len(text) / self._token_estimate_factor)

    def build(
        self,
        query: str,
        chunks: list[DocumentChunk],
        max_tokens: int = 4000,
    ) -> str:
        """Assemble a context string from chunks, staying within the token limit.

        Chunks are included in order of their ``chunk_index``, up to the
        ``max_tokens`` budget. If the budget is exceeded, remaining chunks
        are silently dropped and a warning is logged.

        Args:
            query: The original user query (included as a header).
            chunks: Retrieved document chunks, ideally pre-sorted by relevance.
            max_tokens: Maximum token count for the assembled context.

        Returns:
            A single string containing the query header and included chunks.
        """
        parts: list[str] = []
        used_tokens = self._estimate_tokens(query)

        # Reserve tokens for the query header
        header = f"## Context for: {query}\n\n"
        parts.append(header)

        for chunk in chunks:
            chunk_tokens = self._estimate_tokens(chunk.content)
            if used_tokens + chunk_tokens > max_tokens:
                logger.warning(
                    "Context budget exceeded (%d / %d tokens). Dropping %d chunk(s).",
                    used_tokens,
                    max_tokens,
                    len(chunks) - len(parts) + 1,
                )
                break

            parts.append(f"---\n{chunk.content}\n")
            used_tokens += chunk_tokens

        result = "".join(parts)
        logger.debug("Built context of ~%d estimated tokens", used_tokens)
        return result
