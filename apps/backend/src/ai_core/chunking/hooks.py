"""Hook system for the chunking pipeline.

Allows registering callbacks that fire at specific lifecycle events:

- ``before_chunking``: After validation, before the chunker runs.
- ``after_chunking``: After the chunker produces chunks, before validation.
- ``before_validation``: Before the validation engine runs.
- ``after_validation``: After validation completes, before returning.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from shared.models.processing import ParsedDocument

from src.ai_core.chunking.models import ChunkingResult

logger = logging.getLogger(__name__)


class HookEvent(str, Enum):
    """Lifecycle events that hooks can attach to."""

    BEFORE_CHUNKING = "before_chunking"
    AFTER_CHUNKING = "after_chunking"
    BEFORE_VALIDATION = "before_validation"
    AFTER_VALIDATION = "after_validation"


# Type aliases for hook callbacks
BeforeChunkingHook = Callable[[ParsedDocument], ParsedDocument]
AfterChunkingHook = Callable[[ChunkingResult], ChunkingResult]
BeforeValidationHook = Callable[[ChunkingResult], ChunkingResult]
AfterValidationHook = Callable[[ChunkingResult], ChunkingResult]

# Union of all hook callback types
HookCallback = BeforeChunkingHook | AfterChunkingHook | BeforeValidationHook | AfterValidationHook


@dataclass
class ChunkingHook:
    """A single hook registration.

    Attributes:
        name: Human-readable identifier for this hook (for logging).
        event: The lifecycle event this hook fires on.
        callback: The callable to invoke.
        once: If ``True``, auto-unregister after first invocation.
    """

    name: str
    event: HookEvent
    callback: HookCallback
    once: bool = False


@dataclass
class _HookEntry:
    hook: ChunkingHook
    fired: bool = False


class HookRegistry:
    """Registry of chunking lifecycle hooks.

    Hooks are stored per-event and executed in registration order.
    A hook with ``once=True`` is removed after its first invocation.
    """

    def __init__(self) -> None:
        self._hooks: dict[HookEvent, list[_HookEntry]] = {
            event: [] for event in HookEvent
        }

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        event: HookEvent | str,
        callback: HookCallback,
        name: str | None = None,
        once: bool = False,
    ) -> None:
        """Register a callback for a lifecycle event.

        Args:
            event: The event (``HookEvent`` enum or string name).
            callback: The callable to invoke.  Must match the event's
                      signature (see ``HookEvent`` docstrings).
            name: Optional human-readable name (auto-generated if omitted).
            once: If ``True``, the hook fires once then is removed.
        """
        if isinstance(event, str):
            event = HookEvent(event)

        hook = ChunkingHook(
            name=name or f"{event.value}_hook_{len(self._hooks[event]) + 1}",
            event=event,
            callback=callback,
            once=once,
        )
        self._hooks[event].append(_HookEntry(hook=hook))
        logger.debug("Registered hook '%s' for event %s", hook.name, event.value)

    def unregister(self, name: str) -> bool:
        """Remove a hook by name.  Returns ``True`` if found and removed."""
        for entries in self._hooks.values():
            for i, entry in enumerate(entries):
                if entry.hook.name == name:
                    entries.pop(i)
                    logger.debug("Unregistered hook '%s'", name)
                    return True
        return False

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run_before_chunking(self, document: ParsedDocument) -> ParsedDocument:
        """Run all ``BEFORE_CHUNKING`` hooks."""
        return self._run(HookEvent.BEFORE_CHUNKING, document)

    def run_after_chunking(self, result: ChunkingResult) -> ChunkingResult:
        """Run all ``AFTER_CHUNKING`` hooks."""
        return self._run(HookEvent.AFTER_CHUNKING, result)

    def run_before_validation(self, result: ChunkingResult) -> ChunkingResult:
        """Run all ``BEFORE_VALIDATION`` hooks."""
        return self._run(HookEvent.BEFORE_VALIDATION, result)

    def run_after_validation(self, result: ChunkingResult) -> ChunkingResult:
        """Run all ``AFTER_VALIDATION`` hooks."""
        return self._run(HookEvent.AFTER_VALIDATION, result)

    def _run(self, event: HookEvent, arg: Any) -> Any:
        """Execute all hooks for *event* in registration order."""
        to_remove: list[int] = []
        for i, entry in enumerate(self._hooks[event]):
            if entry.fired and entry.hook.once:
                continue
            try:
                logger.debug("Running hook '%s' on event %s", entry.hook.name, event.value)
                arg = entry.hook.callback(arg)
                entry.fired = True
                if entry.hook.once:
                    to_remove.append(i)
            except Exception:
                logger.exception("Hook '%s' failed on event %s", entry.hook.name, event.value)
        # Remove one-shot hooks (reverse index to preserve order)
        for i in reversed(to_remove):
            self._hooks[event].pop(i)
        return arg

    def list_hooks(self, event: HookEvent | None = None) -> list[ChunkingHook]:
        """List registered hooks, optionally filtered by event."""
        if event:
            return [entry.hook for entry in self._hooks[event]]
        return [
            entry.hook for entries in self._hooks.values() for entry in entries
        ]

    def clear(self) -> None:
        """Remove all hooks."""
        for entries in self._hooks.values():
            entries.clear()
