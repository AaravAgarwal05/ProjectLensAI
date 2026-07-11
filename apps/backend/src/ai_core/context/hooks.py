"""Hook system for context assembly pipeline.

Events:
- ``before_context``: Before context assembly begins.
- ``after_context``: After context is assembled.
- ``before_budget``: Before budget allocation.
- ``after_budget``: After budget allocation.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from src.ai_core.context.models import ContextChunk, ConversationMessage, LLMContext

logger = logging.getLogger(__name__)


class ContextHookEvent(StrEnum):
    """Lifecycle events that context hooks can attach to."""

    BEFORE_CONTEXT = "before_context"
    AFTER_CONTEXT = "after_context"
    BEFORE_BUDGET = "before_budget"
    AFTER_BUDGET = "after_budget"


BeforeContextHook = Callable[
    [str, list[ContextChunk], list[ConversationMessage]],
    tuple[str, list[ContextChunk], list[ConversationMessage]]
    | Awaitable[tuple[str, list[ContextChunk], list[ConversationMessage]]],
]
AfterContextHook = Callable[[LLMContext], LLMContext | Awaitable[LLMContext]]
BeforeBudgetHook = Callable[[LLMContext], LLMContext | Awaitable[LLMContext]]
AfterBudgetHook = Callable[[LLMContext], LLMContext | Awaitable[LLMContext]]

ContextHookCallback = BeforeContextHook | AfterContextHook | BeforeBudgetHook | AfterBudgetHook


@dataclass
class ContextHook:
    """A single hook registration."""

    name: str
    event: ContextHookEvent
    callback: ContextHookCallback
    once: bool = False


@dataclass
class _HookEntry:
    hook: ContextHook
    fired: bool = False


class ContextHookRegistry:
    """Registry of context assembly lifecycle hooks."""

    def __init__(self) -> None:
        self._hooks: dict[ContextHookEvent, list[_HookEntry]] = {
            event: [] for event in ContextHookEvent
        }

    def register(
        self,
        event: ContextHookEvent | str,
        callback: ContextHookCallback,
        name: str | None = None,
        once: bool = False,
    ) -> None:
        if isinstance(event, str):
            event = ContextHookEvent(event)
        hook = ContextHook(
            name=name or f"{event.value}_hook_{len(self._hooks[event]) + 1}",
            event=event,
            callback=callback,
            once=once,
        )
        self._hooks[event].append(_HookEntry(hook=hook))
        logger.debug("Registered context hook '%s' for event %s", hook.name, event.value)

    def unregister(self, name: str) -> bool:
        for entries in self._hooks.values():
            for i, entry in enumerate(entries):
                if entry.hook.name == name:
                    entries.pop(i)
                    return True
        return False

    async def run_before_context(
        self, query: str, chunks: list[ContextChunk], history: list[ConversationMessage]
    ) -> tuple[str, list[ContextChunk], list[ConversationMessage]]:
        q, c, h = await self._run(ContextHookEvent.BEFORE_CONTEXT, query, chunks, history)
        return q, c, h

    async def run_after_context(self, ctx: LLMContext) -> LLMContext:
        out = await self._run(ContextHookEvent.AFTER_CONTEXT, ctx)
        return out if isinstance(out, LLMContext) else ctx

    async def run_before_budget(self, ctx: LLMContext) -> LLMContext:
        out = await self._run(ContextHookEvent.BEFORE_BUDGET, ctx)
        return out if isinstance(out, LLMContext) else ctx

    async def run_after_budget(self, ctx: LLMContext) -> LLMContext:
        out = await self._run(ContextHookEvent.AFTER_BUDGET, ctx)
        return out if isinstance(out, LLMContext) else ctx

    async def _run(self, event: ContextHookEvent, *args: Any) -> Any:
        results = list(args)
        for i, entry in enumerate(self._hooks[event]):
            if entry.fired and entry.hook.once:
                continue
            try:
                if len(results) > 1:
                    results = await entry.hook.callback(*results)  # type: ignore[misc]
                else:
                    results = await entry.hook.callback(results[0])  # type: ignore[call-arg,misc]
                if not isinstance(results, tuple):
                    results = (results,)  # type: ignore[assignment]
                entry.fired = True
                if entry.hook.once:
                    self._hooks[event].pop(i)
            except Exception:
                logger.exception(
                    "Context hook '%s' failed on event %s",
                    entry.hook.name,
                    event.value,
                )
        return results if len(results) > 1 else results[0]

    def list_hooks(self, event: ContextHookEvent | None = None) -> list[ContextHook]:
        if event:
            return [entry.hook for entry in self._hooks[event]]
        return [entry.hook for entries in self._hooks.values() for entry in entries]

    def clear(self) -> None:
        for entries in self._hooks.values():
            entries.clear()
