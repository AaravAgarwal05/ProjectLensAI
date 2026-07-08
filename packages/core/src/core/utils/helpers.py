"""Utility helper functions."""

import re
from datetime import datetime, timezone


def snake_to_camel(s: str) -> str:
    """Convert ``snake_case`` to ``camelCase``.

    >>> snake_to_camel("hello_world")
    'helloWorld'
    """
    components = s.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def camel_to_snake(s: str) -> str:
    """Convert ``camelCase`` to ``snake_case``.

    >>> camel_to_snake("helloWorld")
    'hello_world'
    """
    pattern = re.compile(r"(?<!^)(?=[A-Z])")
    return pattern.sub("_", s).lower()


def truncate(s: str, max_len: int) -> str:
    """Truncate *s* to *max_len* characters, appending ``...`` if cut.

    >>> truncate("hello world", 8)
    'hello...'
    """
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


def now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def deep_merge(base: dict, override: dict) -> dict:
    """Deep-merge two dictionaries.  Values in *override* win.

    Nested dictionaries are merged recursively; other values are
    overwritten.
    """
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
