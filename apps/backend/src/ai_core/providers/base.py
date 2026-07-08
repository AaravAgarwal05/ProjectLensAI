"""Abstract base for AI model providers."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any


class BaseAIProvider(ABC):
    """Interface for external AI providers (e.g. OpenAI, Anthropic, Ollama).

    Concrete subclasses implement actual API calls and handle provider-
    specific authentication, retry logic, and error mapping.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name (e.g. ``"openai"``, ``"anthropic"``)."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """The default model identifier (e.g. ``"gpt-4o"``, ``"claude-3-opus"``)."""

    @property
    @abstractmethod
    def api_key(self) -> str:
        """The API key used to authenticate with the provider."""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Send a prompt and return the generated text.

        Args:
            prompt: The input prompt.
            **kwargs: Provider-specific parameters (temperature, max_tokens, etc.).

        Returns:
            The generated text response.
        """

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Send a prompt and stream the generated text token by token.

        Args:
            prompt: The input prompt.
            **kwargs: Provider-specific parameters.

        Yields:
            Partial text chunks as they become available.
        """

    @abstractmethod
    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Generate an embedding vector for the given text.

        Args:
            text: Input text to embed.
            **kwargs: Provider-specific parameters.

        Returns:
            A list of floats representing the embedding.
        """
