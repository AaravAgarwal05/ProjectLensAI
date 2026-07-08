"""PDF document parser using PyMuPDF."""

import logging
import time
from datetime import datetime, timezone
from typing import Any

from shared.models.processing import (
    DocumentMetadata,
    Page,
    ParsedDocument,
    ProcessingStatistics,
    ProcessingWarning,
)
from src.document_processing.exceptions import ParseError
from src.document_processing.parsers.base import BaseParser

logger = logging.getLogger(__name__)

try:
    import fitz
except ImportError as exc:
    raise ImportError(
        "PyMuPDF is required for PDF parsing. "
        "Install it with: pip install pymupdf"
    ) from exc


class PDFParser(BaseParser):
    """Parse PDF documents and extract per-page text content using PyMuPDF."""

    @property
    def name(self) -> str:
        return "pdf"

    @classmethod
    def supported_formats(cls) -> list[str]:
        return ["pdf"]

    async def parse(self, file_path: str) -> ParsedDocument:
        """Extract text from a PDF file.

        Args:
            file_path: Absolute path to the PDF file.

        Returns:
            A ParsedDocument with per-page text and metadata.

        Raises:
            ParseError: If the document cannot be opened or parsed.
        """
        start_time = time.monotonic()
        warnings: list[ProcessingWarning] = []

        # --- Open the document ---
        try:
            doc = fitz.open(file_path)
        except Exception as exc:
            raise ParseError(
                message=f"Failed to open PDF: {exc}",
                details={"file_path": file_path, "error": str(exc)},
            ) from exc

        # --- Detect encrypted PDFs early ---
        if doc.is_encrypted:
            doc.close()
            raise ParseError(
                message="Cannot parse encrypted PDF document",
                details={"file_path": file_path},
            )

        try:
            # --- Extract metadata from PyMuPDF doc.metadata ---
            raw_meta: dict[str, Any] = doc.metadata or {}
            title = raw_meta.get("title") or None
            author = raw_meta.get("author") or None
            subject = raw_meta.get("subject") or None
            keywords_raw = raw_meta.get("keywords") or ""
            keywords = _parse_keywords(keywords_raw)

            # --- Extract pages ---
            pages: list[Page] = []
            raw_text_parts: list[str] = []
            total_char_count = 0
            total_word_count = 0

            for page_num in range(len(doc)):
                page_obj = doc[page_num]
                text = page_obj.get_text()
                # Handle non-UTF-8 edge case gracefully
                if not isinstance(text, str):
                    text = str(text, errors="replace")
                char_count = len(text)
                word_count = len(text.split())
                total_char_count += char_count
                total_word_count += word_count
                raw_text_parts.append(text)

                pages.append(
                    Page(
                        number=page_num + 1,
                        content=text,
                        char_count=char_count,
                        word_count=word_count,
                    )
                )

            # Handle empty document edge case
            if not pages:
                warnings.append(
                    ProcessingWarning(
                        stage="parse",
                        message="PDF document contains no extractable pages",
                        details={"file_path": file_path},
                    )
                )

            raw_text = "".join(raw_text_parts)

            # --- Build DocumentMetadata (never fails; missing = None) ---
            metadata = DocumentMetadata(
                title=title,
                author=author,
                subject=subject,
                keywords=keywords,
                page_count=len(pages) or None,
                word_count=total_word_count,
                char_count=total_char_count,
                creation_date=_try_parse_pdf_date(raw_meta.get("creationDate")),
                modification_date=_try_parse_pdf_date(raw_meta.get("modDate")),
                processed_by=self.name,
                extra={
                    "format": "PDF",
                    "pdf_version": raw_meta.get("format", ""),
                },
            )

            # --- Build ProcessingStatistics ---
            elapsed = (time.monotonic() - start_time) * 1000
            statistics = ProcessingStatistics(
                parse_time_ms=elapsed,
                total_time_ms=elapsed,
                page_count=len(pages),
                raw_char_count=total_char_count,
                clean_char_count=total_char_count,
            )

            return ParsedDocument(
                parser_used=self.name,
                metadata=metadata,
                pages=pages,
                raw_text=raw_text,
                clean_text=raw_text,
                warnings=warnings,
                statistics=statistics,
            )

        except ParseError:
            raise
        except Exception as exc:
            raise ParseError(
                message=f"Failed to parse PDF content: {exc}",
                details={"file_path": file_path, "error": str(exc)},
            ) from exc
        finally:
            doc.close()


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _parse_keywords(raw: str) -> list[str]:
    """Split a comma- or semicolon-separated keyword string into a clean list."""
    if not raw:
        return []
    return [k.strip() for k in raw.replace(";", ",").split(",") if k.strip()]


def _try_parse_pdf_date(date_str: str | None) -> datetime | None:
    """Try to parse a PDF date string (e.g. ``D:20230101120000Z``).

    PDF date format: ``D:YYYYMMDDHHmmSSOHH'mm'``
    We extract the datetime portion and ignore the timezone offset to keep
    parsing robust — metadata extraction must never raise.
    """
    if not date_str:
        return None
    try:
        cleaned = date_str.strip()
        if cleaned.startswith("D:"):
            cleaned = cleaned[2:]
        # Take at least the first 14 digits: YYYYMMDDHHmmSS
        cleaned = cleaned[:14]
        if len(cleaned) < 14:
            return None
        dt = datetime(
            int(cleaned[0:4]),
            int(cleaned[4:6]),
            int(cleaned[6:8]),
            int(cleaned[8:10]),
            int(cleaned[10:12]),
            int(cleaned[12:14]),
            tzinfo=timezone.utc,
        )
        return dt
    except (ValueError, IndexError):
        return None
