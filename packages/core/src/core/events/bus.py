"""Thread-safe event bus."""

import asyncio
import inspect
import threading
from collections.abc import Awaitable, Callable

from core.events.types import Event, EventHandler
from core.utils.singleton import Singleton


class EventBus(metaclass=Singleton):
    """Thread-safe singleton event bus for publish/subscribe."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler to an event type."""
        with self._lock:
            self._handlers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type."""
        with self._lock:
            handlers = self._handlers.get(event_type, [])
            if handler in handlers:
                handlers.remove(handler)

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribed handlers.

        Synchronous handlers are called immediately.  Asynchronous
        handlers are scheduled via ``asyncio.create_task``.
        """
        handlers = list(self._handlers.get(event.name, []))
        for handler in handlers:
            result = handler(event)
            if isinstance(result, Awaitable):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(result)
                except RuntimeError:
                    # No running event loop — create a temporary one
                    asyncio.run(result)

    def clear(self) -> None:
        """Remove all subscribers."""
        with self._lock:
            self._handlers.clear()
