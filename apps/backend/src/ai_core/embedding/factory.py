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
    "default": "sentence_transformers",
}


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
