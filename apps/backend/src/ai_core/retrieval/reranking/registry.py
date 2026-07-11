"""Reranker registry — maps reranker names to reranker classes."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.ai_core.retrieval.exceptions import RerankerNotFoundError

if TYPE_CHECKING:
    from src.ai_core.retrieval.reranking.base import Reranker

logger = logging.getLogger(__name__)


class RerankerRegistry:
    """Map of human-readable names to ``Reranker`` *classes*.

    Lazy instantiation — instances are cached on first ``get()``.
    """

    def __init__(self) -> None:
        self._classes: dict[str, type[Reranker]] = {}
        self._instances: dict[str, Reranker] = {}

    def register(
        self,
        name: str,
        reranker_cls: type[Reranker],
        /,
        *,
        overwrite: bool = False,
    ) -> None:
        normalised = name.lower().strip()
        if normalised in self._classes and not overwrite:
            raise ValueError(
                f"Reranker '{normalised}' is already registered. " f"Use overwrite=True to replace."
            )
        self._classes[normalised] = reranker_cls
        self._instances.pop(normalised, None)
        logger.debug("Registered reranker '%s' -> %s", normalised, reranker_cls.__name__)

    def get(self, name: str, /, **kwargs: object) -> Reranker:
        normalised = name.lower().strip()
        cls = self._classes.get(normalised)
        if cls is None:
            raise RerankerNotFoundError(
                f"No reranker registered under name '{normalised}'. "
                f"Available: {list(self._classes)}"
            )
        if normalised not in self._instances:
            self._instances[normalised] = cls(**kwargs)
        return self._instances[normalised]

    def list_names(self) -> list[str]:
        return list(self._classes.keys())

    def create_all(self, **kwargs: object) -> list[Reranker]:
        result: list[Reranker] = []
        for name in self._classes:
            result.append(self.get(name, **kwargs))
        return result

    def unregister(self, name: str) -> None:
        normalised = name.lower().strip()
        self._classes.pop(normalised, None)
        self._instances.pop(normalised, None)
