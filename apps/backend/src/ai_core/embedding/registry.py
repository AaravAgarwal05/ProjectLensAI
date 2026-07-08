"""Embedding registry — maps provider names to provider classes.

Plugin-driven: add a new provider by registering it here.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.ai_core.embedding.exceptions import ProviderNotFoundError

if TYPE_CHECKING:
    from src.ai_core.embedding.base import EmbeddingProvider

logger = logging.getLogger(__name__)


class EmbeddingRegistry:
    """Map of human-readable names to ``EmbeddingProvider`` *classes*.

    Registration uses **lazy instantiation** — instances are created on
    first ``get()`` call and then cached.
    """

    def __init__(self) -> None:
        self._classes: dict[str, type[EmbeddingProvider]] = {}
        self._instances: dict[str, EmbeddingProvider] = {}

    # -- public interface ---------------------------------------------------

    def register(
        self,
        name: str,
        provider_cls: type[EmbeddingProvider],
        /,
        *,
        overwrite: bool = False,
    ) -> None:
        """Register a provider class under *name*.

        Args:
            name: Human-readable provider name (case-insensitive).
            provider_cls: The provider class (not an instance).
            overwrite: If True, replace an existing registration.

        Raises:
            ValueError: If *name* is already registered and *overwrite* is False.
        """
        normalised = name.lower().strip()
        if normalised in self._classes and not overwrite:
            raise ValueError(
                f"Provider '{normalised}' is already registered. " f"Use overwrite=True to replace."
            )
        self._classes[normalised] = provider_cls
        self._instances.pop(normalised, None)
        logger.debug("Registered embedding provider '%s' -> %s", normalised, provider_cls.__name__)

    def get(
        self,
        name: str,
        /,
        **kwargs: object,
    ) -> EmbeddingProvider:
        """Return a (cached) provider instance for *name*.

        Args:
            name: Provider name registered via :meth:`register`.
            **kwargs: Optional keyword arguments passed to the constructor
                      on first instantiation.

        Returns:
            A cached ``EmbeddingProvider`` instance.

        Raises:
            ProviderNotFoundError: If *name* is not registered.
        """
        normalised = name.lower().strip()
        cls = self._classes.get(normalised)
        if cls is None:
            raise ProviderNotFoundError(
                f"No provider registered under name '{normalised}'. "
                f"Available: {list(self._classes)}"
            )
        if normalised not in self._instances:
            self._instances[normalised] = cls(**kwargs)
        return self._instances[normalised]

    def list_names(self) -> list[str]:
        """Return all registered provider names."""
        return list(self._classes.keys())

    def create_all(self, **kwargs: object) -> list[EmbeddingProvider]:
        """Return one instance of every registered provider."""
        result: list[EmbeddingProvider] = []
        for name in self._classes:
            result.append(self.get(name, **kwargs))
        return result

    def unregister(self, name: str) -> None:
        """Remove a provider registration (no-op if missing)."""
        normalised = name.lower().strip()
        self._classes.pop(normalised, None)
        self._instances.pop(normalised, None)
