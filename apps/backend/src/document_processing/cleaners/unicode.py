"""Unicode cleaner — normalisation, typographic replacements, invisible-char removal."""

import re
import unicodedata

from src.document_processing.cleaners.base import TextCleaner


class UnicodeCleaner(TextCleaner):
    """Apply NFKC normalisation, replace typographic punctuation with ASCII
    equivalents, and strip zero-width / invisible characters."""

    # Typographic replacements (curly quotes, dashes, ellipsis)
    _TYPOGRAPHIC_REPLACEMENTS: dict[str, str] = {
        "“": '"',  # left double quotation mark
        "”": '"',  # right double quotation mark
        "„": '"',  # double low-9 quotation mark
        "‘": "'",  # left single quotation mark
        "’": "'",  # right single quotation mark
        "‚": "'",  # single low-9 quotation mark
        "–": "-",  # en dash
        "—": "--",  # em dash
        "…": "...",  # horizontal ellipsis
        "·": "*",  # middle dot (used as bullet)
        "•": "*",  # bullet
    }

    # Zero-width / invisible characters to strip entirely
    _INVISIBLE_RE = re.compile(
        "["
        "​"  # zero-width space
        "‌"  # zero-width non-joiner
        "‍"  # zero-width joiner
        "‎"  # left-to-right mark
        "‏"  # right-to-left mark
        "⁠"  # word joiner
        "⁡"  # function application
        "⁢"  # invisible times
        "⁣"  # invisible separator
        "⁤"  # invisible plus
        "﻿"  # BOM / zero-width no-break space
        "]"
    )

    def clean(self, text: str) -> str:
        """Normalise, replace typographic chars, and remove invisible chars."""
        # NFKC normalisation first
        text = unicodedata.normalize("NFKC", text)

        # Replace typographic punctuation
        for old, new in self._TYPOGRAPHIC_REPLACEMENTS.items():
            text = text.replace(old, new)

        # Strip invisible characters
        text = self._INVISIBLE_RE.sub("", text)

        return text

    @property
    def name(self) -> str:
        return "unicode"
