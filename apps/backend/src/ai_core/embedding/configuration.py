"""Embedding configuration — defines parameters for every provider."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EmbeddingConfiguration:
    """Configuration for embedding providers.

    Sensible defaults are provided for every parameter.

    Attributes:
        provider: Default provider name (``"sentence_transformers"``).
        model_name: Default model name (``"BAAI/bge-small-en-v1.5"``).
        batch_size: Max texts per batch (default: 32).
        device: Torch device (``"cpu"``, ``"cuda"``). Default ``"cpu"``.
        normalize_embeddings: Whether to L2-normalize output vectors.
        cache_folder: Model cache directory (optional).
        ollama_base_url: Ollama server URL (default: ``"http://localhost:11434"``).
        ollama_model: Ollama model name (default: ``"nomic-embed-text"``).
        timeout: HTTP request timeout in seconds (default: 60).
        extra: Provider-specific overrides.
    """

    provider: str = "sentence_transformers"
    model_name: str = "BAAI/bge-small-en-v1.5"
    batch_size: int = 32
    device: str = "cpu"
    normalize_embeddings: bool = True
    cache_folder: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "nomic-embed-text"
    timeout: int = 60
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def default(cls) -> EmbeddingConfiguration:
        """Return a default configuration."""
        return cls()

    def merge(self, overrides: dict[str, Any]) -> EmbeddingConfiguration:
        """Return a new configuration with *overrides* applied."""
        merged = {**self.__dict__, **overrides}
        return EmbeddingConfiguration(**merged)
