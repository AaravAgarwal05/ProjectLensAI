"""Document metadata extraction using the shared pydantic DocumentMetadata model."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from shared.models.processing import DocumentMetadata

logger = logging.getLogger(__name__)

# ── language-detection helpers ──────────────────────────────────────────

_COMMON_ENGLISH_WORDS: frozenset[str] = frozenset({
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "it",
    "for", "not", "on", "with", "he", "as", "you", "do", "at", "this",
    "but", "his", "by", "from", "they", "we", "say", "her", "she", "or",
    "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "is", "are", "was", "were", "been", "being", "has", "had", "did",
    "can", "may", "than", "then", "them", "these", "those", "just",
    "also", "very", "when", "where", "how", "each", "other", "some",
    "such", "only", "own", "same", "too", "after", "before",
})


class MetadataExtractor:
    """Extracts rich document metadata.

    The extractor is stateless and composable.  It returns a pydantic
    ``DocumentMetadata`` instance, never raises, and accepts an optional
    ``parser_metadata`` dict for overrides from specialised parsers.
    """

    @staticmethod
    def extract(
        file_path: str,
        content: str,
        parser_metadata: dict[str, Any] | None = None,
    ) -> DocumentMetadata:
        """Extract metadata from a document file and its text content.

        Parameters
        ----------
        file_path:
            Absolute path to the document.
        content:
            Full text content of the document.
        parser_metadata:
            Optional dictionary of metadata extracted by a specialised parser
            (e.g. PDF properties, DOCX metadata).  Values in this dict take
            precedence over auto-derived values.

        Returns
        -------
        DocumentMetadata
            A populated ``DocumentMetadata`` instance.  Missing values are
            ``None`` or sensible defaults — never raises.
        """
        pm = parser_metadata or {}
        path = Path(file_path)

        stat_result = _safe_stat(path)

        title = pm.get("title") or _derive_title_from_filename(path)
        author = pm.get("author")
        subject = pm.get("subject")
        keywords = pm.get("keywords", [])
        language = pm.get("language") or _detect_language(content)
        page_count = pm.get("page_count")
        word_count = len(content.split())
        char_count = len(content)
        creation_date = _parse_timestamp(
            pm.get("creation_date")
            or (
                datetime.fromtimestamp(stat_result.st_ctime)
                if stat_result
                else None
            ),
        )
        modification_date = _parse_timestamp(
            pm.get("modification_date")
            or (
                datetime.fromtimestamp(stat_result.st_mtime)
                if stat_result
                else None
            ),
        )
        processed_by = "pipeline-v1"

        # Build extra from parser_metadata minus keys we already consumed.
        extra = dict(pm)
        for key in (
            "title",
            "author",
            "subject",
            "keywords",
            "language",
            "page_count",
            "creation_date",
            "modification_date",
        ):
            extra.pop(key, None)

        # Normalise keywords to a list
        if not isinstance(keywords, list):
            keywords = [str(keywords)] if keywords else []

        return DocumentMetadata(
            title=title,
            author=author,
            subject=subject,
            keywords=keywords,
            language=language,
            page_count=page_count,
            word_count=word_count,
            char_count=char_count,
            creation_date=creation_date,
            modification_date=modification_date,
            processed_by=processed_by,
            extra=extra,
        )


# ── internal helpers ────────────────────────────────────────────────────


def _safe_stat(path: Path) -> Any:
    """Return ``os.stat_result`` or ``None`` (never raises)."""
    try:
        return path.stat()
    except OSError:
        return None


def _derive_title_from_filename(path: Path) -> str:
    """Derive a human-readable title from the file path."""
    stem = path.stem
    name = stem.replace("_", " ").replace("-", " ")
    return name.strip() or path.name


def _detect_language(content: str) -> str | None:
    """Detect language from a text sample using a simple frequency heuristic.

    Currently detects English only; returns ``None`` when unsure.
    """
    if not content.strip():
        return None

    sample = content[:2000]
    words = sample.lower().split()
    if not words:
        return None

    common_count = sum(1 for w in words if w in _COMMON_ENGLISH_WORDS)
    ratio = common_count / len(words)

    return "en" if ratio > 0.15 else None


def _parse_timestamp(value: Any) -> datetime | None:
    """Safely convert a raw value to ``datetime`` or return ``None``."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None
    return None
