"""Abstract base class for context strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.ai_core.context.configuration import ContextConfiguration
from src.ai_core.context.models import (
    ContextChunk,
    ConversationMessage,
    LLMContext,
)


class ContextStrategy(ABC):
    """Plugin-based strategy for assembling LLM context."""

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Human-readable strategy name."""

    @abstractmethod
    async def assemble(
        self,
        query: str,
        chunks: list[ContextChunk],
        history: list[ConversationMessage],
        config: ContextConfiguration,
    ) -> LLMContext:
        """Assemble context from query, chunks, and conversation history."""

    @abstractmethod
    def configure(self, params: dict[str, Any]) -> None:
        """Apply runtime configuration overrides."""
