"""Generic Factory — creates objects from registered builders."""

from collections.abc import Callable
from typing import Any


class Factory:
    """A generic factory that creates objects from registered builders.

    Unlike the singleton registries, there can be multiple independent
    Factory instances.
    """

    def __init__(self) -> None:
        self._builders: dict[str, Callable[..., Any]] = {}

    def register(self, key: str, builder: Callable[..., Any]) -> None:
        """Register a *builder* callable under *key*."""
        self._builders[key] = builder

    def create(self, key: str, **kwargs: Any) -> Any:
        """Create an object for *key*, passing *kwargs* to the builder.

        Raises:
            KeyError: If *key* is not registered.
        """
        builder = self._builders.get(key)
        if builder is None:
            msg = f"Factory has no builder registered for '{key}'"
            raise KeyError(msg)
        return builder(**kwargs)

    def keys(self) -> list[str]:
        """Return all registered keys."""
        return list(self._builders.keys())

    def unregister(self, key: str) -> None:
        """Remove a registered builder by *key*."""
        self._builders.pop(key, None)
