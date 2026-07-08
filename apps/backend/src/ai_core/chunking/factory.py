"""Chunking factory — create chunkers from configuration.

The factory decouples chunker instantiation from the caller.
It works with ``ChunkingRegistry`` to resolve named strategies.
"""

from __future__ import annotations

from typing import Any

from src.ai_core.chunking.base import ChunkingStrategy
from src.ai_core.chunking.configuration import ChunkingConfiguration
from src.ai_core.chunking.registry import ChunkingRegistry

_STRATEGY_NAMES: dict[str, str] = {
    "fixed": "fixed",
    "recursive": "recursive",
    "heading_aware": "heading_aware",
    "heading-aware": "heading_aware",
    "default": "heading_aware",
}


class ChunkingFactory:
    """Creates chunker instances from configuration.

    Examples
    --------
    .. code-block:: python

        factory = ChunkingFactory(registry)
        chunker = factory.create("heading_aware")
        chunker = factory.create_from_config("fixed", {"chunk_size": 500})
    """

    def __init__(self, registry: ChunkingRegistry | None = None) -> None:
        """Initialize the factory.

        Args:
            registry: A ``ChunkingRegistry``.  If ``None``, a new empty
                      registry is created and must be populated before use.
        """
        self._registry = registry or ChunkingRegistry()

    @property
    def registry(self) -> ChunkingRegistry:
        """The backing registry."""
        return self._registry

    def create(
        self,
        name: str,
        /,
        **kwargs: Any,
    ) -> ChunkingStrategy:
        """Create (or retrieve a cached) chunker by strategy name.

        Args:
            name: Strategy name (``"fixed"``, ``"recursive"``,
                  ``"heading_aware"``).
            **kwargs: Optional keyword arguments forwarded to the
                      chunker constructor.

        Returns:
            A ``ChunkingStrategy`` instance.
        """
        resolved = _STRATEGY_NAMES.get(name.lower().strip(), name)
        return self._registry.get(resolved, **kwargs)

    def create_from_config(
        self,
        config: ChunkingConfiguration,
        /,
    ) -> ChunkingStrategy:
        """Create a chunker from a ``ChunkingConfiguration``.

        Uses the configuration's ``extra`` dict to determine which
        strategy to load (key ``"strategy"``, default ``"heading_aware"``).

        Args:
            config: A ``ChunkingConfiguration`` instance.

        Returns:
            A configured ``ChunkingStrategy`` instance.
        """
        strategy_name = config.extra.get("strategy", "heading_aware")
        chunker = self._registry.get(strategy_name)
        chunker.configure(config.extra)
        return chunker

    def create_all(self, **kwargs: Any) -> list[ChunkingStrategy]:
        """Return one instance of every registered chunker.

        Args:
            **kwargs: Forwarded to chunker constructors.

        Returns:
            A list of ``ChunkingStrategy`` instances.
        """
        return self._registry.create_all(**kwargs)

    def available_strategies(self) -> list[str]:
        """Return the list of registered strategy names."""
        return self._registry.list_names()
