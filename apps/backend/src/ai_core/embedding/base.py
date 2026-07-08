"""Abstract embedding provider interface.

Every embedding provider implements ``EmbeddingProvider``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class EmbeddingProvider(ABC):
    """Interface for text-to-vector embedding models.

    Subclasses wrap specific providers (Sentence-Transformers, Ollama,
    etc.) and normalise their output.
    """

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text string.

        Args:
            text: Input text to embed.

        Returns:
            A list of floats representing the embedding.
        """

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts.

        Subclasses should override with a provider-native batch API
        for efficiency.  The default here calls ``embed`` sequentially.

        Args:
            texts: List of input strings to embed.

        Returns:
            A list of embedding vectors, one per input string.
        """

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """The dimensionality of the embedding vectors produced."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identifier of the underlying embedding model."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier."""

    async def health_check(self) -> bool:
        """Check whether the provider is reachable and operational.

        Returns ``True`` if healthy, ``False`` otherwise.
        """
        return True

    @abstractmethod
    def configure(self, params: dict[str, Any]) -> None:
        """Reconfigure the provider at runtime.

        Args:
            params: Provider-specific configuration keys.
        """
