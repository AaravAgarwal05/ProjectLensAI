"""Prompt Builder — converts LLMContext into structured prompt text."""

from __future__ import annotations

from typing import Any

from src.ai_core.context.models import LLMContext
from src.ai_core.llm.configuration import LLMConfiguration
from src.ai_core.llm.models import LLMRequest


class PromptBuilder:
    """Assembles system and user prompts from an LLMContext.

    The builder does not interact with retrieval, vector stores, or
    document processing.  It only transforms the already-assembled
    context into prompt text.
    """

    def __init__(self, config: LLMConfiguration | None = None) -> None:
        self._config = config or LLMConfiguration.default()

    def build(
        self,
        ctx: LLMContext,
        overrides: dict[str, Any] | None = None,
    ) -> LLMRequest:
        """Convert an LLMContext into an LLMRequest.

        Args:
            ctx: The assembled context from the Context Manager.
            overrides: Optional overrides for temperature, max_tokens, etc.

        Returns:
            An LLMRequest ready for an LLMProvider.
        """
        system_prompt = self._build_system_prompt(ctx)
        user_prompt = self._build_user_prompt(ctx)
        citations = self._collect_citations(ctx)

        temperature = self._config.temperature
        max_tokens = self._config.max_tokens
        top_p = self._config.top_p
        model_name = self._config.model_name

        if overrides:
            temperature = overrides.get("temperature", temperature)
            max_tokens = overrides.get("max_tokens", max_tokens)
            top_p = overrides.get("top_p", top_p)
            model_name = overrides.get("model_name", model_name)

        return LLMRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            model_name=model_name,
            metadata={"citations": citations, "num_chunks": len(ctx.chunks)},
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_system_prompt(self, ctx: LLMContext) -> str:
        """Assemble the system-level prompt."""
        parts: list[str] = []

        base = ctx.system_prompt or self._config.system_prompt
        parts.append(base)

        # Inject metadata about the context
        meta_lines: list[str] = []
        if ctx.metadata.strategy:
            meta_lines.append(f"Strategy: {ctx.metadata.strategy}")
        if ctx.metadata.num_chunks:
            meta_lines.append(f"Context chunks: {ctx.metadata.num_chunks}")
        if ctx.metadata.num_messages:
            meta_lines.append(f"Conversation turns: {ctx.metadata.num_messages}")

        if meta_lines:
            parts.append("---")
            parts.extend(meta_lines)

        return "\n".join(parts)

    def _build_user_prompt(self, ctx: LLMContext) -> str:
        """Assemble the user-facing prompt including context and history."""
        parts: list[str] = []

        # Query
        if ctx.query:
            parts.append(f"Query: {ctx.query}")

        # Conversation summary (if available)
        if ctx.conversation_summary and ctx.conversation_summary.text:
            parts.append(f"Earlier conversation summary: {ctx.conversation_summary.text}")

        # Conversation history (trimmed)
        if ctx.conversation_history:
            history_lines = [f"{msg.role}: {msg.content}" for msg in ctx.conversation_history]
            parts.append("Conversation history:\n" + "\n".join(history_lines))

        # Context chunks
        if ctx.chunks:
            chunk_parts: list[str] = []
            for i, chunk in enumerate(ctx.chunks):
                header = f"[Chunk {i + 1}]"
                if chunk.section_name:
                    header += f" ({chunk.section_name})"
                if chunk.source_title:
                    header += f" — {chunk.source_title}"
                chunk_parts.append(f"{header}\n{chunk.content}")
            parts.append("Retrieved context:\n" + "\n\n".join(chunk_parts))

        return "\n\n".join(parts)

    def _collect_citations(self, ctx: LLMContext) -> list[str]:
        """Collect all unique citations from context chunks."""
        seen: set[str] = set()
        citations: list[str] = []
        for chunk in ctx.chunks:
            for c in chunk.citations:
                if c not in seen:
                    seen.add(c)
                    citations.append(c)
        return citations
