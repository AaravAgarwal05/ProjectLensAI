"""Token estimation utility.

Uses ``tiktoken`` for accurate token counting when available,
falls back to a rough ``chars/4`` estimate.
"""

from __future__ import annotations

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

_CHARS_PER_TOKEN = 4  # rough fallback ratio

# Prefer cl100k_base — close enough for most English/mixed text.
# Gracefully degrade if tiktoken is not installed.
try:
    import tiktoken

    _TOKENIZER = tiktoken.get_encoding("cl100k_base")
except ImportError:
    _TOKENIZER = None
    logger.info("tiktoken not available — falling back to chars/4 estimation")


@lru_cache(maxsize=4096)
def estimate_tokens(text: str) -> int:
    """Return the estimated token count for *text*.

    Uses ``tiktoken`` (``cl100k_base``) when available, otherwise
    falls back to ``len(text) // 4``.
    """
    if not text:
        return 0
    if _TOKENIZER is not None:
        return max(1, len(_TOKENIZER.encode(text, disallowed_special=())))
    return max(1, len(text) // _CHARS_PER_TOKEN)
