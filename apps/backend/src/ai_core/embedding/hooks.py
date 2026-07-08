"""Hook system for the embedding pipeline.

Allows registering callbacks at specific lifecycle events:

- ``before_embedding``: Before the embedding run starts.
- ``after_embedding``: After all chunks are embedded.
- ``before_batch``: Before each batch is sent to the provider.
- ``after_batch``: After each batch is processed.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast

from src.ai_core.chunking.models import Chunk
from src.ai_core.embedding.models import EmbeddedChunk, EmbeddingResult

logger = logging.getLogger(__name__)


class EmbeddingHookEvent(StrEnum):
    """Lifecycle events that hooks can attach to."""

    BEFORE_EMBEDDING = "before_embedding"
    AFTER_EMBEDDING = "after_embedding"
    BEFORE_BATCH = "before_batch"
    AFTER_BATCH = "after_batch"


# Type aliases
BeforeEmbeddingHook = Callable[[list[Chunk]], list[Chunk]]
AfterEmbeddingHook = Callable[[EmbeddingResult], EmbeddingResult]
BeforeBatchHook = Callable[[list[Chunk]], list[Chunk]]
AfterBatchHook = Callable[[list[Chunk], list[EmbeddedChunk]], list[EmbeddedChunk]]

EmbeddingHookCallback = BeforeEmbeddingHook | AfterEmbeddingHook | BeforeBatchHook | AfterBatchHook


@dataclass
class EmbeddingHook:
    """A single hook registration."""

    name: str
    event: EmbeddingHookEvent
    callback: EmbeddingHookCallback
    once: bool = False


@dataclass
class _HookEntry:
    hook: EmbeddingHook
    fired: bool = False


class EmbeddingHookRegistry:
    """Registry of embedding lifecycle hooks."""

    def __init__(self) -> None:
        self._hooks: dict[EmbeddingHookEvent, list[_HookEntry]] = {
            event: [] for event in EmbeddingHookEvent
        }

    def register(
        self,
        event: EmbeddingHookEvent | str,
        callback: EmbeddingHookCallback,
        name: str | None = None,
        once: bool = False,
    ) -> None:
        """Register a callback for a lifecycle event."""
        if isinstance(event, str):
            event = EmbeddingHookEvent(event)

        hook = EmbeddingHook(
            name=name or f"{event.value}_hook_{len(self._hooks[event]) + 1}",
            event=event,
            callback=callback,
            once=once,
        )
        self._hooks[event].append(_HookEntry(hook=hook))
        logger.debug("Registered hook '%s' for event %s", hook.name, event.value)

    def unregister(self, name: str) -> bool:
        """Remove a hook by name."""
        for entries in self._hooks.values():
            for i, entry in enumerate(entries):
                if entry.hook.name == name:
                    entries.pop(i)
                    return True
        return False

    def run_before_embedding(self, chunks: list[Chunk]) -> list[Chunk]:
        """Run all BEFORE_EMBEDDING hooks."""
        result = self._run(EmbeddingHookEvent.BEFORE_EMBEDDING, chunks)
        return chunks if not isinstance(result, list) else result

    def run_after_embedding(self, result: EmbeddingResult) -> EmbeddingResult:
        """Run all AFTER_EMBEDDING hooks."""
        out = self._run(EmbeddingHookEvent.AFTER_EMBEDDING, result)
        return result if not isinstance(out, EmbeddingResult) else out

    def run_before_batch(self, chunks: list[Chunk]) -> list[Chunk]:
        """Run all BEFORE_BATCH hooks."""
        result = self._run(EmbeddingHookEvent.BEFORE_BATCH, chunks)
        return chunks if not isinstance(result, list) else result

    def run_after_batch(
        self, chunks: list[Chunk], embeddings: list[EmbeddedChunk]
    ) -> list[EmbeddedChunk]:
        """Run all AFTER_BATCH hooks."""
        result = self._run(EmbeddingHookEvent.AFTER_BATCH, (chunks, embeddings))
        if isinstance(result, tuple):
            return cast(list[EmbeddedChunk], result[1])
        return embeddings

    def _run(self, event: EmbeddingHookEvent, arg: Any) -> Any:
        """Execute all hooks for *event* in registration order."""
        to_remove: list[int] = []
        for i, entry in enumerate(self._hooks[event]):
            if entry.fired and entry.hook.once:
                continue
            try:
                arg = entry.hook.callback(arg)  # type: ignore[call-arg]
                entry.fired = True
                if entry.hook.once:
                    to_remove.append(i)
            except Exception:
                logger.exception("Hook '%s' failed on event %s", entry.hook.name, event.value)
        for i in reversed(to_remove):
            self._hooks[event].pop(i)
        return arg

    def list_hooks(self, event: EmbeddingHookEvent | None = None) -> list[EmbeddingHook]:
        """List registered hooks, optionally filtered by event."""
        if event:
            return [entry.hook for entry in self._hooks[event]]
        return [entry.hook for entries in self._hooks.values() for entry in entries]

    def clear(self) -> None:
        """Remove all hooks."""
        for entries in self._hooks.values():
            entries.clear()
