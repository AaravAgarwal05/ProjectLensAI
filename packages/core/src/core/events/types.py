"""Event type definitions."""

from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

import pydantic


class Event(pydantic.BaseModel):
    """A named event carrying data and metadata."""

    name: str = pydantic.Field(description="Event type identifier")
    data: dict[str, Any] = pydantic.Field(default_factory=dict, description="Event payload")
    source: str = pydantic.Field(default="", description="Component that published the event")
    timestamp: datetime = pydantic.Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the event was created",
    )


EventHandler = Callable[[Event], Awaitable[None] | None]
"""Type alias for event handler callables.

Handlers may be synchronous or asynchronous.
"""
