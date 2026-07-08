"""Abstract document parser interface."""

from abc import ABC, abstractmethod

from shared.models.processing import ParsedDocument


class BaseParser(ABC):
    """Interface for document format parsers.

    Each subclass handles one or more file formats and extracts
    human-readable text from binary or structured documents.
    """

    @abstractmethod
    async def parse(self, file_path: str) -> ParsedDocument:
        """Parse a document file and extract its content.

        Args:
            file_path: Path to the document on disk.

        Returns:
            A ParsedDocument with extracted content, pages, and metadata.
        """

    @classmethod
    @abstractmethod
    def supported_formats(cls) -> list[str]:
        """Return the file extensions this parser can handle (e.g. ``["pdf"]``)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique parser identifier (e.g. ``"pdf"``, ``"docx"``)."""
