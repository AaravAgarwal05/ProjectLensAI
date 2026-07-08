"""Plain-text and markdown document parser."""

import logging
import time
from pathlib import Path

from shared.models.processing import (
    DocumentMetadata,
    Page,
    ParsedDocument,
    ProcessingStatistics,
)

from src.document_processing.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class TextParser(BaseParser):
    """Parse plain-text, markdown and CSV files.

    Reads the entire file as UTF-8 text and returns it as a single-page
    parsed document.
    """

    @property
    def name(self) -> str:
        return "text"

    @classmethod
    def supported_formats(cls) -> list[str]:
        return ["txt", "md", "csv"]

    async def parse(self, file_path: str) -> ParsedDocument:
        """Read a text file and extract its content.

        Args:
            file_path: Absolute path to the text file.

        Returns:
            A ParsedDocument with the file contents.

        Raises:
            FileNotFoundError: If the file does not exist.
            ParseError: If the file cannot be decoded.
        """
        start_time = time.monotonic()
        path = Path(file_path)

        content = path.read_text(encoding="utf-8")
        logger.debug("Parsed text file %s (%d chars)", file_path, len(content))

        lines = content.splitlines()
        char_count = len(content)
        word_count = len(content.split())

        pages = [
            Page(
                number=1,
                content=content,
                char_count=char_count,
                word_count=word_count,
            )
        ]

        metadata = DocumentMetadata(
            title=path.stem,
            page_count=1,
            word_count=word_count,
            char_count=char_count,
            processed_by=self.name,
            extra={
                "line_count": len(lines),
                "extension": path.suffix,
            },
        )

        elapsed = (time.monotonic() - start_time) * 1000
        statistics = ProcessingStatistics(
            parse_time_ms=elapsed,
            total_time_ms=elapsed,
            page_count=1,
            raw_char_count=char_count,
            clean_char_count=char_count,
        )

        return ParsedDocument(
            parser_used=self.name,
            metadata=metadata,
            pages=pages,
            raw_text=content,
            clean_text=content,
            statistics=statistics,
        )
