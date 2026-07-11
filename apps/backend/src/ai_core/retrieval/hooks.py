"""Hook system for the retrieval pipeline.

Events:
- ``before_retrieval``: Before candidate retrieval from the store.
- ``after_retrieval``: After candidates are retrieved.
- ``before_reranking``: Before reranking pass.
- ``after_reranking``: After reranking is complete.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from src.ai_core.retrieval.models import RetrievalResult, RetrievedChunk, SearchQuery

logger = logging.getLogger(__name__)


class RetrievalHookEvent(StrEnum):
    """Lifecycle events that hooks can attach to."""

    BEFORE_RETRIEVAL = "before_retrieval"
    AFTER_RETRIEVAL = "after_retrieval"
    BEFORE_RERANKING = "before_reranking"
    AFTER_RERANKING = "after_reranking"


BeforeRetrievalHook = Callable[[SearchQuery], SearchQuery | Awaitable[SearchQuery]]
AfterRetrievalHook = Callable[
    [list[RetrievedChunk]], list[RetrievedChunk] | Awaitable[list[RetrievedChunk]]
]
BeforeRerankingHook = Callable[
    [list[RetrievedChunk]], list[RetrievedChunk] | Awaitable[list[RetrievedChunk]]
]
AfterRerankingHook = Callable[[RetrievalResult], RetrievalResult | Awaitable[RetrievalResult]]

RetrievalHookCallback = (
    BeforeRetrievalHook | AfterRetrievalHook | BeforeRerankingHook | AfterRerankingHook
)


@dataclass
class RetrievalHook:
    """A single hook registration."""

    name: str
    event: RetrievalHookEvent
    callback: RetrievalHookCallback
    once: bool = False


@dataclass
class _HookEntry:
    hook: RetrievalHook
    fired: bool = False


class RetrievalHookRegistry:
    """Registry of retrieval lifecycle hooks."""

    def __init__(self) -> None:
        self._hooks: dict[RetrievalHookEvent, list[_HookEntry]] = {
            event: [] for event in RetrievalHookEvent
        }

    def register(
        self,
        event: RetrievalHookEvent | str,
        callback: RetrievalHookCallback,
        name: str | None = None,
        once: bool = False,
    ) -> None:
        if isinstance(event, str):
            event = RetrievalHookEvent(event)
        hook = RetrievalHook(
            name=name or f"{event.value}_hook_{len(self._hooks[event]) + 1}",
            event=event,
            callback=callback,
            once=once,
        )
        self._hooks[event].append(_HookEntry(hook=hook))
        logger.debug("Registered hook '%s' for event %s", hook.name, event.value)

    def unregister(self, name: str) -> bool:
        for entries in self._hooks.values():
            for i, entry in enumerate(entries):
                if entry.hook.name == name:
                    entries.pop(i)
                    return True
        return False

    async def run_before_retrieval(self, query: SearchQuery) -> SearchQuery:
        out = await self._run(RetrievalHookEvent.BEFORE_RETRIEVAL, query)
        return query if not isinstance(out, SearchQuery) else out

    async def run_after_retrieval(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        out = await self._run(RetrievalHookEvent.AFTER_RETRIEVAL, chunks)
        return chunks if not isinstance(out, list) else out

    async def run_before_reranking(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        out = await self._run(RetrievalHookEvent.BEFORE_RERANKING, chunks)
        return chunks if not isinstance(out, list) else out

    async def run_after_reranking(self, result: RetrievalResult) -> RetrievalResult:
        out = await self._run(RetrievalHookEvent.AFTER_RERANKING, result)
        return result if not isinstance(out, RetrievalResult) else out

    async def _run(self, event: RetrievalHookEvent, arg: Any) -> Any:
        to_remove: list[int] = []
        for i, entry in enumerate(self._hooks[event]):
            if entry.fired and entry.hook.once:
                continue
            try:
                arg = await entry.hook.callback(arg)  # type: ignore[misc]
                entry.fired = True
                if entry.hook.once:
                    to_remove.append(i)
            except Exception:
                logger.exception("Hook '%s' failed on event %s", entry.hook.name, event.value)
        for i in reversed(to_remove):
            self._hooks[event].pop(i)
        return arg

    def list_hooks(self, event: RetrievalHookEvent | None = None) -> list[RetrievalHook]:
        if event:
            return [entry.hook for entry in self._hooks[event]]
        return [entry.hook for entries in self._hooks.values() for entry in entries]

    def clear(self) -> None:
        for entries in self._hooks.values():
            entries.clear()
