"""Vector-store registry — maps store names to store classes.

Plugin-driven: add a new store by registering it here.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.ai_core.vector_store.exceptions import StoreNotFoundError

if TYPE_CHECKING:
    from src.ai_core.vector_store.base import VectorStore

logger = logging.getLogger(__name__)


class VectorStoreRegistry:
    """Map of human-readable names to ``VectorStore`` *classes*.

    Registration uses **lazy instantiation** — instances are created on
    first ``get()`` call and then cached.
    """

    def __init__(self) -> None:
        self._classes: dict[str, type[VectorStore]] = {}
        self._instances: dict[str, VectorStore] = {}

    def register(
        self,
        name: str,
        store_cls: type[VectorStore],
        /,
        *,
        overwrite: bool = False,
    ) -> None:
        """Register a store class under *name*.

        Args:
            name: Human-readable store name (case-insensitive).
            store_cls: The store class (not an instance).
            overwrite: If True, replace an existing registration.
        """
        normalised = name.lower().strip()
        if normalised in self._classes and not overwrite:
            raise ValueError(
                f"Store '{normalised}' is already registered. " f"Use overwrite=True to replace."
            )
        self._classes[normalised] = store_cls
        self._instances.pop(normalised, None)
        logger.debug("Registered store '%s' -> %s", normalised, store_cls.__name__)

    def get(
        self,
        name: str,
        /,
        **kwargs: object,
    ) -> VectorStore:
        """Return a (cached) store instance for *name*."""
        normalised = name.lower().strip()
        cls = self._classes.get(normalised)
        if cls is None:
            raise StoreNotFoundError(
                f"No store registered under name '{normalised}'. "
                f"Available: {list(self._classes)}"
            )
        if normalised not in self._instances:
            self._instances[normalised] = cls(**kwargs)
        return self._instances[normalised]

    def list_names(self) -> list[str]:
        """Return all registered store names."""
        return list(self._classes.keys())

    def create_all(self, **kwargs: object) -> list[VectorStore]:
        """Return one instance of every registered store."""
        result: list[VectorStore] = []
        for name in self._classes:
            result.append(self.get(name, **kwargs))
        return result

    def unregister(self, name: str) -> None:
        """Remove a store registration (no-op if missing)."""
        normalised = name.lower().strip()
        self._classes.pop(normalised, None)
        self._instances.pop(normalised, None)
