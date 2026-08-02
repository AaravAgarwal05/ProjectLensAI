"""Embedding factory — create providers from configuration.

The factory decouples provider instantiation from the caller.
"""

from __future__ import annotations

from typing import Any

from src.ai_core.embedding.base import EmbeddingProvider
from src.ai_core.embedding.configuration import EmbeddingConfiguration
from src.ai_core.embedding.registry import EmbeddingRegistry

_PROVIDER_ALIASES: dict[str, str] = {
    "sentence_transformers": "sentence_transformers",
    "sentence-transformer": "sentence_transformers",
    "st": "sentence_transformers",
    "ollama": "ollama",
    "gemini": "gemini",
    "google": "gemini",
    "default": "sentence_transformers",
}


_default_embedding_registry: EmbeddingRegistry | None = None


def default_embedding_registry() -> EmbeddingRegistry:
    """Return a shared registry with every bundled embedding provider."""
    global _default_embedding_registry  # noqa: PLW0603
    if _default_embedding_registry is None:
        from src.ai_core.embedding.providers.gemini import GeminiEmbeddingProvider
        from src.ai_core.embedding.providers.ollama import OllamaEmbeddingProvider
        from src.ai_core.embedding.providers.sentence_transformer import (
            SentenceTransformerProvider,
        )

        _default_embedding_registry = EmbeddingRegistry()
        _default_embedding_registry.register("sentence_transformer", SentenceTransformerProvider)
        _default_embedding_registry.register("ollama", OllamaEmbeddingProvider)
        _default_embedding_registry.register("gemini", GeminiEmbeddingProvider)
    return _default_embedding_registry


def build_embedding_provider(config: EmbeddingConfiguration | None = None) -> EmbeddingProvider:
    """Create the configured embedding provider — the single selection point.

    Call sites never construct providers directly; they ask for "the
    configured one" and get it. Provider-specific defaults (Ollama
    URL/model, Gemini model) are threaded the same way ``EmbeddingPipeline``
    does, so selection is pure configuration.

    Args:
        config: Provider configuration. ``EmbeddingConfiguration.default()``
                when omitted (currently ``gemini``).
    """
    cfg = config or EmbeddingConfiguration.default()
    factory = EmbeddingFactory(default_embedding_registry())
    provider = factory.create(cfg.provider)
    params = dict(cfg.extra)
    if cfg.provider == "ollama":
        params.setdefault("base_url", cfg.ollama_base_url)
        params.setdefault("model_name", cfg.ollama_model)
    elif cfg.provider == "gemini":
        params.setdefault("model_name", cfg.gemini_model)
    provider.configure(params)
    return provider


class EmbeddingFactory:
    """Creates embedding provider instances from configuration.

    Examples
    --------
    .. code-block:: python

        factory = EmbeddingFactory(registry)
        provider = factory.create("sentence_transformers")
        provider = factory.create_from_config(config)
    """

    def __init__(self, registry: EmbeddingRegistry | None = None) -> None:
        """Initialize the factory.

        Args:
            registry: An ``EmbeddingRegistry``. If ``None``, a new empty
                      registry is created.
        """
        self._registry = registry or EmbeddingRegistry()

    @property
    def registry(self) -> EmbeddingRegistry:
        """The backing registry."""
        return self._registry

    def create(
        self,
        name: str,
        /,
        **kwargs: Any,
    ) -> EmbeddingProvider:
        """Create (or retrieve a cached) provider by name.

        Args:
            name: Provider name.
            **kwargs: Optional keyword arguments forwarded to the constructor.

        Returns:
            An ``EmbeddingProvider`` instance.
        """
        resolved = _PROVIDER_ALIASES.get(name.lower().strip(), name)
        return self._registry.get(resolved, **kwargs)

    def create_from_config(
        self,
        config: EmbeddingConfiguration,
        /,
    ) -> EmbeddingProvider:
        """Create a provider from an ``EmbeddingConfiguration``."""
        provider_name = config.provider
        provider = self._registry.get(provider_name)
        provider.configure(config.extra)
        return provider

    def create_all(self, **kwargs: Any) -> list[EmbeddingProvider]:
        """Return one instance of every registered provider."""
        return self._registry.create_all(**kwargs)

    def available_providers(self) -> list[str]:
        """Return the list of registered provider names."""
        return self._registry.list_names()
