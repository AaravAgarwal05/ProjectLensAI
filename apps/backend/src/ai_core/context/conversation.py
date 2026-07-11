"""Conversation manager — handles history, summarization, trimming."""

from __future__ import annotations

import logging
from typing import Any

from src.ai_core.context.configuration import ContextConfiguration
from src.ai_core.context.models import (
    ConversationMessage,
    ConversationSummary,
)

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """Rough token estimation (4 chars per token)."""
    return len(text) // 4


class ConversationManager:
    """Manages conversation history for context assembly."""

    def __init__(self, config: ContextConfiguration | None = None) -> None:
        self._config = config or ContextConfiguration.default()

    @property
    def config(self) -> ContextConfiguration:
        return self._config

    def configure(self, params: dict[str, Any]) -> None:
        self._config = self._config.merge(params)

    def prepare(
        self,
        history: list[ConversationMessage],
    ) -> tuple[list[ConversationMessage], ConversationSummary | None]:
        """Prepare conversation: trim, summarize, return messages + optional summary."""
        if not history:
            return [], None

        trimmed = self._trim_history(history)
        summary = None
        if (
            self._config.enable_conversation_summary
            and len(history) > self._config.conversation_max_messages
        ):
            summary = self._summarize(history)

        return trimmed, summary

    def _trim_history(
        self,
        history: list[ConversationMessage],
    ) -> list[ConversationMessage]:
        """Keep the most recent messages within limits."""
        if len(history) <= self._config.conversation_max_messages:
            return history

        tokens_used = 0
        trimmed: list[ConversationMessage] = []

        for msg in reversed(history):
            tokens = estimate_tokens(msg.content)
            if tokens_used + tokens > self._config.max_history_tokens:
                break
            trimmed.insert(0, msg)
            tokens_used += tokens

        return trimmed

    def _summarize(
        self,
        history: list[ConversationMessage],
    ) -> ConversationSummary:
        """Build summary of older messages (no LLM — heuristic)."""
        total_tokens = 0
        messages: list[str] = []

        for i, msg in enumerate(history[: -self._config.conversation_max_messages]):
            prefix = f"{msg.role}: " if i % 2 == 0 else ""
            messages.append(f"{prefix}{msg.content[:200]}")
            total_tokens += len(messages[-1]) // 4

        text = " | ".join(messages) if messages else ""

        return ConversationSummary(
            text=text,
            token_count=total_tokens,
            message_count=len(messages),
        )
