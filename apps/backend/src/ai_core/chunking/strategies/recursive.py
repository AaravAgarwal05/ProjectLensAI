"""Recursive chunker — tries multiple split levels in priority order.

Priority order (highest → lowest):
  1. Heading (##, Chapter N, Section N.)
  2. Paragraph (double newline)
  3. Sentence (. ! ?)
  4. Word (space)
  5. Character

At each level the chunker splits the text, then recursively checks
whether any resulting segment still exceeds ``chunk_size`` and splits
again at the next level down.  This preserves semantic boundaries
wherever possible.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from shared.models.processing import ParsedDocument

from src.ai_core.chunking.base import ChunkingStrategy
from src.ai_core.chunking.configuration import ChunkingConfiguration
from src.ai_core.chunking.models import Chunk, ChunkMetadata, ChunkingResult

logger = logging.getLogger(__name__)


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


# Regex for detecting common headings
_HEADING_RE = re.compile(
    r"^(?:#{1,6}\s+|(?:[A-Z]\.\s*)+|"
    r"(?:CHAPTER|Chapter|chapter|SECTION|Section|section)\s+\d+[\.\s]|"
    r"\d+\.\d+\s+|^\d+\.\s+)",
    re.MULTILINE,
)


class RecursiveChunker(ChunkingStrategy):
    """Recursively splits text at semantic boundaries.

    The chunker maintains a priority list of split levels.  It splits
    at the highest-priority level first, then recursively splits any
    segment that still exceeds the target chunk size at the next level.
    """

    # Level names in priority order (index 0 = highest priority)
    LEVELS = ["heading", "paragraph", "sentence", "word", "character"]

    def __init__(
        self,
        config: ChunkingConfiguration | None = None,
    ) -> None:
        self._config = config or ChunkingConfiguration.default()
        self._name = "recursive"

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

        # Start recursion at the highest level (heading)
        raw_segments = self._split_recursive(
            text=text,
            level_index=0,
            chunk_size=cfg.chunk_size,
            min_chunk_size=cfg.min_chunk_size,
        )

        # Build Chunk objects
        chunks: list[Chunk] = []
        offset = 0

        for i, seg in enumerate(raw_segments):
            seg_text = seg.strip() if cfg.strip_whitespace else seg
            if not seg_text:
                offset += len(seg)
                continue

            if len(seg_text) < cfg.min_chunk_size:
                # Merge tiny chunks into previous chunk if possible
                if chunks:
                    prev = chunks.pop()
                    merged_text = prev.text + "\n" + seg_text
                    merged_text = merged_text.strip()
                    merged_chunk = Chunk(
                        chunk_index=prev.chunk_index,
                        report_id=prev.report_id,
                        report_version_id=prev.report_version_id,
                        start_offset=prev.start_offset,
                        end_offset=offset + len(seg),
                        text=merged_text,
                        token_count=_estimate_tokens(merged_text),
                        page_number=prev.page_number,
                        metadata=prev.metadata,
                    )
                    chunks.append(merged_chunk)
                    offset += len(seg)
                    continue

            page = self._estimate_page(document, offset)
            metadata = ChunkMetadata(
                page_number=page,
                source=self._name,
                document_title=document.metadata.title,
                document_author=document.metadata.author,
                language=document.metadata.language,
            )
            chunk = Chunk(
                chunk_index=len(chunks),
                report_id=document.report_id,
                report_version_id=document.version_id,
                start_offset=offset,
                end_offset=offset + len(seg),
                text=seg_text,
                token_count=_estimate_tokens(seg_text),
                page_number=page,
                metadata=metadata,
            )
            chunks.append(chunk)
            offset += len(seg)

        result = ChunkingResult(chunks=chunks, warnings=warnings)
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
    # Recursive splitting
    # ------------------------------------------------------------------

    def _split_recursive(
        self,
        text: str,
        level_index: int,
        chunk_size: int,
        min_chunk_size: int,
    ) -> list[str]:
        """Recursively split *text* into sub-segments.

        Args:
            text: The text to split.
            level_index: Current level index in ``self.LEVELS``.
            chunk_size: Target chunk size in characters.
            min_chunk_size: Minimum allowed segment length.

        Returns:
            A list of text segments.
        """
        # If the text fits within the target, return it as-is
        if len(text) <= chunk_size:
            return [text] if text.strip() else []

        level = self.LEVELS[level_index] if level_index < len(self.LEVELS) else "character"
        segments = self._split_at_level(text, level)

        # If no segments were produced (separator not found), fall through
        # to the next level
        if not segments or len(segments) == 1:
            next_level = level_index + 1
            if next_level < len(self.LEVELS):
                return self._split_recursive(
                    text, next_level, chunk_size, min_chunk_size
                )
            # Character-level: hard split
            return self._hard_split(text, chunk_size)

        # Recurse on any segment that still exceeds chunk_size
        result: list[str] = []
        for seg in segments:
            if len(seg) > chunk_size and level_index + 1 < len(self.LEVELS):
                result.extend(
                    self._split_recursive(
                        seg, level_index + 1, chunk_size, min_chunk_size
                    )
                )
            elif len(seg) > chunk_size:
                result.extend(self._hard_split(seg, chunk_size))
            else:
                if seg.strip():
                    result.append(seg)

        return result

    def _split_at_level(self, text: str, level: str) -> list[str]:
        """Split *text* at the given level. Returns a list of segments."""
        if level == "heading":
            return self._split_by_heading(text)
        elif level == "paragraph":
            return [s for s in text.split("\n\n") if s.strip()] or [text]
        elif level == "sentence":
            return re.split(r"(?<=[.!?])\s+", text)
        elif level == "word":
            # Split by spaces, then rejoin to approximate word groupings
            return [s for s in text.split(" ") if s.strip()] or [text]
        elif level == "character":
            return list(text)
        return [text]

    @staticmethod
    def _split_by_heading(text: str) -> list[str]:
        """Split text at detected heading boundaries.

        Uses ``_HEADING_RE`` to find heading lines.  Each heading
        starts a new segment (the heading is *included* in its segment).
        """
        matches = list(_HEADING_RE.finditer(text))
        if not matches:
            return [text]

        segments: list[str] = []
        prev_end = 0

        for m in matches:
            # Include any text before this heading
            if m.start() > prev_end:
                before = text[prev_end : m.start()]
                if before.strip():
                    segments.append(before)
            prev_end = m.start()

        # Remainder after the last heading
        if prev_end < len(text):
            remaining = text[prev_end:]
            if remaining.strip():
                segments.append(remaining)

        return segments

    @staticmethod
    def _hard_split(text: str, chunk_size: int) -> list[str]:
        """Hard character-level split with no overlap."""
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _estimate_page(document: ParsedDocument, offset: int) -> int | None:
        if not document.pages:
            return None
        cumulative = 0
        for page in document.pages:
            cumulative += len(page.content)
            if offset < cumulative:
                return page.number
        return document.pages[-1].number
