"""Cleaner registry — maps names to cleaner classes.

Use the registry to compose a ``CleaningPipeline`` from named cleaners
at runtime.
"""

import builtins
import logging
from typing import TYPE_CHECKING

from src.document_processing.exceptions import CleanerNotFoundError

if TYPE_CHECKING:
    from src.document_processing.cleaners.base import CleaningPipeline, TextCleaner

logger = logging.getLogger(__name__)


class CleanerRegistry:
    """Map of human-readable names to ``TextCleaner`` *classes* (lazy
    instantiation).

    This is **not** a singleton — multiple registries may exist in the same
    process.

    Examples
    --------
    .. code-block:: python

        registry = CleanerRegistry()
        registry.register("whitespace", WhitespaceCleaner)
        registry.register("unicode", UnicodeCleaner)

        cleaner = registry.get("whitespace")   # lazy instance
        pipeline = registry.create_pipeline(["whitespace", "unicode"])
    """

    def __init__(self) -> None:
        self._classes: dict[str, type[TextCleaner]] = {}
        self._instances: dict[str, TextCleaner] = {}

    # -- public interface ---------------------------------------------------

    def register(self, name: str, cleaner_cls: type["TextCleaner"]) -> None:
        """Register a cleaner class under *name*.

        If *name* is already registered the existing entry is overwritten.
        """
        normalised = name.lower().strip()
        self._classes[normalised] = cleaner_cls
        # Discard cached instance so next get() creates a fresh one.
        self._instances.pop(normalised, None)
        logger.debug("Registered cleaner '%s' -> %s", normalised, cleaner_cls.__name__)

    def get(self, name: str) -> "TextCleaner":
        """Return a (cached) cleaner instance for *name*.

        Instances are created once and reused.
        """
        normalised = name.lower().strip()
        cls = self._classes.get(normalised)
        if cls is None:
            raise CleanerNotFoundError(
                message=f"No cleaner registered under name '{normalised}'",
                details={"name": normalised, "available": list(self._classes)},
            )
        if normalised not in self._instances:
            self._instances[normalised] = cls()
        return self._instances[normalised]

    def list(self) -> list[str]:
        """Return all registered cleaner names in insertion-friendly order."""
        return list(self._classes.keys())

    def create_pipeline(self, names: builtins.list[str]) -> "CleaningPipeline":
        """Return a ``CleaningPipeline`` composed of cleaners in *names* order.

        Raises ``CleanerNotFoundError`` if any name is not registered.
        """
        from src.document_processing.cleaners.base import CleaningPipeline

        cleaners = [self.get(n) for n in names]
        return CleaningPipeline(cleaners=cleaners)
