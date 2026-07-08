"""Chunking registry — maps strategy names to chunker classes.

Plugin-driven: add a new chunker by registering it here.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.ai_core.chunking.exceptions import ChunkerNotFoundError

if TYPE_CHECKING:
    from src.ai_core.chunking.base import ChunkingStrategy

logger = logging.getLogger(__name__)


class ChunkingRegistry:
    """Map of human-readable names to ``ChunkingStrategy`` *classes*.

    Registration uses **lazy instantiation** — instances are created on
    first ``get()`` call and then cached.

    Examples
    --------
    .. code-block:: python

        registry = ChunkingRegistry()
        registry.register("fixed", FixedChunker)
        registry.register("recursive", RecursiveChunker)

        chunker = registry.get("fixed")          # lazy instance
        chunkers = registry.create_all()         # one of each
    """

    def __init__(self) -> None:
        self._classes: dict[str, type[ChunkingStrategy]] = {}
        self._instances: dict[str, ChunkingStrategy] = {}

    # -- public interface ---------------------------------------------------

    def register(
        self,
        name: str,
        chunker_cls: type[ChunkingStrategy],
        /,
        *,
        overwrite: bool = False,
    ) -> None:
        """Register a chunker class under *name*.

        Args:
            name: Human-readable strategy name (case-insensitive).
            chunker_cls: The chunker class (not an instance).
            overwrite: If True, replace an existing registration.

        Raises:
            ValueError: If *name* is already registered and *overwrite* is False.
        """
        normalised = name.lower().strip()
        if normalised in self._classes and not overwrite:
            raise ValueError(
                f"Chunker '{normalised}' is already registered. "
                f"Use overwrite=True to replace."
            )
        self._classes[normalised] = chunker_cls
        self._instances.pop(normalised, None)
        logger.debug("Registered chunker '%s' -> %s", normalised, chunker_cls.__name__)

    def get(
        self,
        name: str,
        /,
        **kwargs: object,
    ) -> ChunkingStrategy:
        """Return a (cached) chunker instance for *name*.

        Args:
            name: Strategy name registered via :meth:`register`.
            **kwargs: Optional keyword arguments passed to the constructor
                      on first instantiation.

        Returns:
            A cached ``ChunkingStrategy`` instance.

        Raises:
            ChunkerNotFoundError: If *name* is not registered.
        """
        normalised = name.lower().strip()
        cls = self._classes.get(normalised)
        if cls is None:
            raise ChunkerNotFoundError(
                f"No chunker registered under name '{normalised}'. "
                f"Available: {list(self._classes)}"
            )
        if normalised not in self._instances:
            self._instances[normalised] = cls(**kwargs)
        return self._instances[normalised]

    def list_names(self) -> list[str]:
        """Return all registered chunker names."""
        return list(self._classes.keys())

    def create_all(self, **kwargs: object) -> list[ChunkingStrategy]:
        """Return one instance of every registered chunker.

        Args:
            **kwargs: Passed to every constructor on first instantiation.

        Returns:
            A list of ``ChunkingStrategy`` instances.
        """
        result: list[ChunkingStrategy] = []
        for name in self._classes:
            result.append(self.get(name, **kwargs))
        return result

    def unregister(self, name: str) -> None:
        """Remove a chunker registration.

        Args:
            name: Strategy name to remove.
        """
        normalised = name.lower().strip()
        self._classes.pop(normalised, None)
        self._instances.pop(normalised, None)
