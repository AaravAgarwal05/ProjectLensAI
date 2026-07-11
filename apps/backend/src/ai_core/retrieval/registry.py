"""Retriever registry — maps retriever names to retriever classes.

Plugin-driven: add a new retriever by registering it here.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.ai_core.retrieval.exceptions import RetrieverNotFoundError

if TYPE_CHECKING:
    from src.ai_core.retrieval.base import Retriever

logger = logging.getLogger(__name__)


class RetrieverRegistry:
    """Map of human-readable names to ``Retriever`` *classes*.

    Registration uses lazy instantiation — instances are created on
    first ``get()`` call and then cached.
    """

    def __init__(self) -> None:
        self._classes: dict[str, type[Retriever]] = {}
        self._instances: dict[str, Retriever] = {}

    def register(
        self,
        name: str,
        retriever_cls: type[Retriever],
        /,
        *,
        overwrite: bool = False,
    ) -> None:
        normalised = name.lower().strip()
        if normalised in self._classes and not overwrite:
            raise ValueError(
                f"Retriever '{normalised}' is already registered. "
                f"Use overwrite=True to replace."
            )
        self._classes[normalised] = retriever_cls
        self._instances.pop(normalised, None)
        logger.debug("Registered retriever '%s' -> %s", normalised, retriever_cls.__name__)

    def get(
        self,
        name: str,
        /,
        **kwargs: object,
    ) -> Retriever:
        normalised = name.lower().strip()
        cls = self._classes.get(normalised)
        if cls is None:
            raise RetrieverNotFoundError(
                f"No retriever registered under name '{normalised}'. "
                f"Available: {list(self._classes)}"
            )
        if normalised not in self._instances:
            self._instances[normalised] = cls(**kwargs)
        return self._instances[normalised]

    def list_names(self) -> list[str]:
        return list(self._classes.keys())

    def create_all(self, **kwargs: object) -> list[Retriever]:
        result: list[Retriever] = []
        for name in self._classes:
            result.append(self.get(name, **kwargs))
        return result

    def unregister(self, name: str) -> None:
        normalised = name.lower().strip()
        self._classes.pop(normalised, None)
        self._instances.pop(normalised, None)
