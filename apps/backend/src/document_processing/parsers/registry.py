"""Parser registry — maps file formats to parser implementations."""

import logging
from collections import UserDict
from typing import TYPE_CHECKING

from src.document_processing.exceptions import ParserNotFoundError

if TYPE_CHECKING:
    from src.document_processing.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class ParserRegistry(UserDict[str, type["BaseParser"]]):
    """Map of file-format extensions to parser *classes* (lazy instantiation).

    This is **not** a singleton — multiple registries may exist in the same
    process (e.g. one for the default pipeline and another for a restricted
    subset of formats).

    Examples
    --------
    .. code-block:: python

        registry = ParserRegistry()
        registry.register(PDFParser)
        registry.register(DOCXParser)

        parser = registry.get("pdf")   # lazy instance
        assert "pdf" in registry
        assert "docx" in registry.list_formats()
    """

    def __init__(self) -> None:
        super().__init__()
        self._instances: dict[str, BaseParser] = {}

    # -- public interface ---------------------------------------------------

    def register(self, parser_cls: type["BaseParser"]) -> None:
        """Register a parser class for every format it supports.

        Args:
            parser_cls: A subclass of ``BaseParser``.

        Raises:
            ValueError: If one of the formats returned by
                ``parser_cls.supported_formats()`` is already registered.
        """
        for fmt in parser_cls.supported_formats():
            normalised = fmt.lower()
            if normalised in self.data:
                logger.warning(
                    "Overwriting parser for .%s: %s -> %s",
                    normalised,
                    type(self.data[normalised]).__name__,
                    parser_cls.__name__,
                )
            self.data[normalised] = parser_cls
            # Discard cached instance so the next get() creates a fresh one.
            self._instances.pop(normalised, None)
            logger.debug("Registered %s for .%s", parser_cls.__name__, normalised)

    def get(self, fmt: str) -> "BaseParser":
        """Return a (cached) parser instance for the given format.

        Instances are created once and reused.
        """
        normalised = fmt.lower()
        cls = self.data.get(normalised)
        if cls is None:
            raise ParserNotFoundError(
                message=f"No parser registered for format '.{normalised}'",
                details={"format": normalised, "available": list(self.data)},
            )
        # Lazy instantiation
        if normalised not in self._instances:
            self._instances[normalised] = cls()
        return self._instances[normalised]

    def list_formats(self) -> list[str]:
        """Return all registered file-extension strings."""
        return list(self.data.keys())

    def unregister(self, fmt: str) -> None:
        """Remove the parser registered for *fmt*.

        This is a no-op if the format is not registered.
        """
        normalised = fmt.lower()
        self.data.pop(normalised, None)
        self._instances.pop(normalised, None)
        logger.debug("Unregistered parser for .%s", normalised)
