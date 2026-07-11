"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from src.ai_core.llm.configuration import LLMConfiguration
from src.ai_core.llm.models import (
    LLMRequest,
    LLMResponse,
    ProviderHealth,
    StreamingChunk,
)


class LLMProvider(ABC):
    """Interface for LLM text-generation providers."""

    def __init__(self, config: LLMConfiguration | None = None) -> None:
        self._config = config or LLMConfiguration.default()

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the unique name of this provider."""

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a complete (non-streaming) response."""

    @abstractmethod
    def generate_stream(self, request: LLMRequest) -> AsyncIterator[StreamingChunk]:
        """Generate a streaming response, yielding chunks."""

    @abstractmethod
    async def check_health(self) -> ProviderHealth:
        """Check if the provider is reachable and the configured model exists."""

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Estimate or retrieve token count for a text string."""

    @abstractmethod
    async def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available on the provider."""

    def configure(self, params: dict[str, Any]) -> None:
        """Apply runtime configuration overrides."""
        self._config = self._config.merge(params)
