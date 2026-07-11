"""LLM provider registry and factory."""

from __future__ import annotations

import logging

from src.ai_core.llm.base import LLMProvider
from src.ai_core.llm.configuration import LLMConfiguration
from src.ai_core.llm.exceptions import ProviderNotFoundError

logger = logging.getLogger(__name__)


class LLMRegistry:
    """Registry of LLM provider classes (lazy instantiation)."""

    def __init__(self) -> None:
        self._providers: dict[str, type[LLMProvider]] = {}
        self._instances: dict[str, LLMProvider] = {}

    def register(self, name: str, provider_cls: type[LLMProvider]) -> None:
        """Register a provider class under *name*."""
        if name in self._providers:
            logger.warning("Overwriting provider '%s'", name)
        self._providers[name] = provider_cls
        self._instances.pop(name, None)
        logger.debug("Registered LLM provider '%s'", name)

    def get(self, name: str) -> LLMProvider:
        """Get or create a provider instance by name."""
        if name not in self._providers:
            raise ProviderNotFoundError(
                f"Unknown provider '{name}'. Registered: {self.list_names()}"
            )
        if name not in self._instances:
            self._instances[name] = self._providers[name]()
            logger.debug("Instantiated provider '%s'", name)
        return self._instances[name]

    def get_class(self, name: str) -> type[LLMProvider]:
        """Return the provider class without instantiating it."""
        if name not in self._providers:
            raise ProviderNotFoundError(
                f"Unknown provider '{name}'. Registered: {self.list_names()}"
            )
        return self._providers[name]

    def unregister(self, name: str) -> None:
        """Remove a provider from the registry."""
        self._providers.pop(name, None)
        self._instances.pop(name, None)
        logger.debug("Unregistered provider '%s'", name)

    def list_names(self) -> list[str]:
        """Return sorted list of registered provider names."""
        return sorted(self._providers)

    def clear(self) -> None:
        """Remove all providers and instances."""
        self._providers.clear()
        self._instances.clear()
        logger.debug("Cleared all providers")


class LLMFactory:
    """Creates LLM providers by name, with alias support."""

    def __init__(self, registry: LLMRegistry | None = None) -> None:
        self._registry = registry or LLMRegistry()
        self._aliases: dict[str, str] = {}

    @property
    def registry(self) -> LLMRegistry:
        return self._registry

    def set_alias(self, alias: str, target: str) -> None:
        """Map *alias* to an existing registered provider *target*."""
        self._aliases[alias] = target
        logger.debug("Alias '%s' -> '%s'", alias, target)

    def resolve(self, name: str) -> str:
        """Resolve an alias to its canonical provider name."""
        return self._aliases.get(name, name)

    def create(self, name: str, config: LLMConfiguration | None = None) -> LLMProvider:
        """Create (or get cached) provider by name, resolving aliases."""
        canonical = self.resolve(name)
        provider = self._registry.get(canonical)
        if config is not None:
            provider.configure(config.to_dict())
        return provider

    def available_providers(self) -> list[str]:
        """Return list of all available provider names (including aliases)."""
        return sorted(set(self._registry.list_names()) | set(self._aliases))
