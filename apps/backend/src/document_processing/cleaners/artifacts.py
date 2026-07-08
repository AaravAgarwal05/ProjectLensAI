"""Page-artifact cleaner — remove page numbers, headers, footers, and
excessive blank lines from digitised documents."""

import re
from collections import Counter

from src.document_processing.cleaners.base import TextCleaner


class PageArtifactCleaner(TextCleaner):
    """Strip page numbers, common header/footer lines, and excessive blank
    lines left behind after removal.

    Heuristic for repeated headers/footers
    --------------------------------------
    The text is split into page-like blocks (by form-feed characters or
    double-newline boundaries). A line that appears as the **first** or
    **last** line of a block in two or more blocks is treated as a likely
    header or footer and removed from that position.
    """

    _PAGE_NUMBER_RE = re.compile(
        r"^(?:\s*[-–—]?\s*\d+\s*[-–—]?\s*|page\s+\d+\s*(?:of\s+\d+)?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    _MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
    _WHITESPACE_ONLY_RE = re.compile(r"^\s*$", re.MULTILINE)

    # Minimum block size to consider for header/footer detection (chars).
    _MIN_BLOCK_LENGTH = 80
    # A line must appear at this position in at least this many blocks.
    _MIN_REPEAT_COUNT = 2

    def clean(self, text: str) -> str:
        """Remove page artifacts and normalise leftover whitespace."""
        # 1. Remove standalone page-number lines.
        text = self._PAGE_NUMBER_RE.sub("", text)

        # 2. Detect and remove repeated headers/footers.
        text = self._remove_repeated_boundary_lines(text)

        # 3. Remove lines that now contain only whitespace.
        text = self._WHITESPACE_ONLY_RE.sub("", text)

        # 4. Collapse 3+ consecutive newlines into 2.
        text = self._MULTI_NEWLINE_RE.sub("\n\n", text)

        return text.strip()

    # ------------------------------------------------------------------
    # Header / footer heuristic
    # ------------------------------------------------------------------

    @staticmethod
    def _split_blocks(text: str) -> list[list[str]]:
        """Split *text* into page-like blocks of lines.

        Uses form-feed (``\\f``) as the primary split delimiter and falls
        back to double-newline boundaries for text without explicit page
        breaks.
        """
        if "\f" in text:
            raw_blocks = text.split("\f")
        else:
            # Treat each group of lines separated by 2+ newlines as a block.
            raw_blocks = re.split(r"\n\n\n+", text)

        blocks: list[list[str]] = []
        for block in raw_blocks:
            lines = block.splitlines()
            # Skip empty blocks and very short blocks.
            if len(block) >= PageArtifactCleaner._MIN_BLOCK_LENGTH and len(lines) > 2:
                blocks.append(lines)
        return blocks

    @staticmethod
    def _find_repeated_lines(
        blocks: list[list[str]],
    ) -> tuple[set[str], set[str]]:
        """Return sets of lines that appear as the first or last line of
        multiple blocks."""
        first_lines: list[str] = []
        last_lines: list[str] = []

        for lines in blocks:
            first = lines[0].strip()
            last = lines[-1].strip()
            if first:
                first_lines.append(first)
            if last:
                last_lines.append(last)

        repeated_first: set[str] = set()
        repeated_last: set[str] = set()

        for counter, target in ((Counter(first_lines), repeated_first), (Counter(last_lines), repeated_last)):
            for line, count in counter.items():
                if count >= PageArtifactCleaner._MIN_REPEAT_COUNT:
                    target.add(line)

        return repeated_first, repeated_last

    @staticmethod
    def _remove_repeated_boundary_lines(text: str) -> str:
        """Remove lines that appear as the first or last line of multiple
        page-like blocks (heuristic header/footer detection)."""
        blocks = PageArtifactCleaner._split_blocks(text)
        if not blocks:
            return text

        repeated_first, repeated_last = PageArtifactCleaner._find_repeated_lines(blocks)

        if not repeated_first and not repeated_last:
            return text

        # Rebuild text, skipping matched header/footer lines.
        out_blocks: list[str] = []
        for lines in blocks:
            filtered = list(lines)
            # Remove trailing footer lines (process from end).
            while filtered and filtered[-1].strip() in repeated_last:
                filtered.pop()
            # Remove leading header lines.
            while filtered and filtered[0].strip() in repeated_first:
                filtered.pop(0)
            if filtered:
                out_blocks.append("\n".join(filtered))

        return "\n\n".join(out_blocks)

    @property
    def name(self) -> str:
        return "page_artifacts"
