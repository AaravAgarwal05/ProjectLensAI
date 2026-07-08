"""Fixed-size chunker — splits text by a fixed character count with overlap.

Configuration:
    chunk_size: Target characters per chunk (default: 1000).
    chunk_overlap: Overlapping characters between chunks (default: 200).
    separator_priority: Ordered list of separators to try (default:
                        double-newline, newline, period, space, character).
"""

from __future__ import annotations

import logging
from typing import Any

from shared.models.processing import ParsedDocument

from src.ai_core.chunking.base import ChunkingStrategy
from src.ai_core.chunking.configuration import ChunkingConfiguration
from src.ai_core.chunking.models import Chunk, ChunkingResult, ChunkMetadata

logger = logging.getLogger(__name__)


def _estimate_tokens(text: str) -> int:
    """Rough token count estimate (4 chars per token)."""
    return max(1, len(text) // 4)


class FixedChunker(ChunkingStrategy):
    """Chunks text by fixed character size with optional overlap.

    For each chunk boundary, the chunker tries the separators in
    *separator_priority* order and splits at the *last* occurrence
    of the first separator found within the window.
    """

    def __init__(
        self,
        config: ChunkingConfiguration | None = None,
    ) -> None:
        self._config = config or ChunkingConfiguration.default()
        self._name = "fixed"

    # ------------------------------------------------------------------
    # ChunkingStrategy interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    def configure(self, params: dict[str, Any]) -> None:
        self._config = self._config.merge(params)

    def validate(self, document: ParsedDocument) -> list[str]:
        warnings: list[str] = []
        if not document.clean_text:
            warnings.append("Document has no clean_text content")
        return warnings

    def chunk(self, document: ParsedDocument) -> ChunkingResult:
        """Split ``document.clean_text`` into fixed-size chunks."""

        warnings = self.validate(document)
        text = document.clean_text

        if not text:
            return ChunkingResult(
                chunks=[],
                warnings=warnings,
                errors=["empty document"],
                successful=False,
            )

        cfg = self._config
        chunk_size = cfg.chunk_size
        overlap = cfg.chunk_overlap
        separators = cfg.separator_priority

        chunks: list[Chunk] = []
        start = 0
        index = 0

        while start < len(text):
            # Determine end boundary for this chunk
            end = min(start + chunk_size, len(text))

            if end < len(text):
                # Try to find a better split point
                end = self._find_split(text, start, end, separators)

            chunk_text = text[start:end].strip()
            if cfg.strip_whitespace:
                chunk_text = chunk_text.strip()

            if chunk_text:
                page = self._estimate_page(document, start)
                metadata = ChunkMetadata(
                    page_number=page,
                    source=self._name,
                    document_title=document.metadata.title,
                    document_author=document.metadata.author,
                    language=document.metadata.language,
                )
                chunk = Chunk(
                    chunk_index=index,
                    report_id=document.report_id,
                    report_version_id=document.version_id,
                    start_offset=start,
                    end_offset=end,
                    text=chunk_text,
                    token_count=_estimate_tokens(chunk_text),
                    page_number=page,
                    metadata=metadata,
                )
                chunks.append(chunk)
                index += 1

            # Advance start, accounting for overlap
            new_start = end - overlap if (end - overlap) > start else end
            start = max(new_start, start + 1)

            # Safety: prevent infinite loop on zero-length advance
            if start >= len(text):
                break

        result = ChunkingResult(chunks=chunks, warnings=warnings)
        # Populate statistics
        sizes = [len(c.text) for c in chunks]
        token_counts = [c.token_count for c in chunks]
        n = len(chunks)
        result.statistics.number_of_chunks = n
        result.statistics.source = self._name
        if n > 0:
            result.statistics.average_chunk_size = sum(sizes) / n
            result.statistics.average_tokens_per_chunk = sum(token_counts) / n
            result.statistics.largest_chunk = max(sizes)
            result.statistics.smallest_chunk = min(sizes)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_split(text: str, start: int, end: int, separators: list[str]) -> int:
        """Find the best split position in ``text[start:end]``.

        Tries each separator in order.  For the first separator found
        within the window, returns the position *after* its *last*
        occurrence.
        """
        window = text[start:end]

        for sep in separators:
            if not sep:
                # Character-level fallback — split at end
                return end
            pos = window.rfind(sep)
            if pos != -1:
                return start + pos + len(sep)

        return end

    @staticmethod
    def _estimate_page(document: ParsedDocument, offset: int) -> int | None:
        """Estimate which page an offset falls on based on page content lengths."""
        if not document.pages:
            return None
        cumulative = 0
        for page in document.pages:
            cumulative += len(page.content)
            if offset < cumulative:
                return page.number  # type: ignore[no-any-return]
        return document.pages[-1].number  # type: ignore[no-any-return]
