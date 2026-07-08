"""Common type aliases and utility generics used across the platform."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, TypeVar

#: Type variable bound to a :class:`Callable`.
CallableT = TypeVar("CallableT", bound=Callable[..., Any])

T = TypeVar("T")
#: Type variable used for generic data wrappers.

#: A dictionary with string keys and arbitrary JSON-serialisable values.
JSONDict = dict[str, Any]

#: A file path expressed as either a string or a :class:`pathlib.Path`.
StrOrPath = str | Path

#: A value that may be either the type ``T`` or an awaitable of ``T``.
AwaitableOrValue = T | Awaitable[T]
