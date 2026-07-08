"""Abstract LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator


class BaseLLMProvider(ABC):
    """Interface for large-language-model providers.

    Subclasses wrap specific APIs (OpenAI, Anthropic, Ollama, etc.)
    and handle authentication, request formatting, and response parsing.
    """

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Send a prompt and return the full generated response.

        Args:
            prompt: The input prompt or message list.
            **kwargs: Provider-specific parameters (temperature, max_tokens, etc.).

        Returns:
            The generated text.
        """

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Send a prompt and stream the response token by token.

        Args:
            prompt: The input prompt or message list.
            **kwargs: Provider-specific parameters.

        Yields:
            Partial text chunks as they become available.
        """

    @abstractmethod
    def supports_streaming(self) -> bool:
        """Indicate whether this provider supports streaming generation."""
