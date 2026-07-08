"""Whitespace cleaner — normalise spacing and line breaks."""

import re

from src.document_processing.cleaners.base import TextCleaner


class WhitespaceCleaner(TextCleaner):
    """Collapse multiple spaces, strip per-line whitespace, and normalise
    consecutive blank lines."""

    _MULTI_SPACE_RE = re.compile(r" {2,}")
    _MULTI_NEWLINE_RE = re.compile(r"\n{3,}")

    def clean(self, text: str) -> str:
        """Apply all whitespace normalisations."""
        # Collapse multiple spaces into one
        text = self._MULTI_SPACE_RE.sub(" ", text)

        # Remove leading / trailing whitespace per line
        text = "\n".join(line.strip() for line in text.splitlines())

        # Collapse 3+ consecutive newlines into 2
        text = self._MULTI_NEWLINE_RE.sub("\n\n", text)

        return text.strip()

    @property
    def name(self) -> str:
        return "whitespace"
