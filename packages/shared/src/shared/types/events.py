"""Type definitions for the platform event bus."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic.main import BaseModel

#: Payload carried by an event, represented as a free-form dictionary.
EventPayload = dict[str, Any]

T = TypeVar("T")


class EventData(BaseModel, Generic[T]):
    """A typed wrapper around event data.

    Attributes:
        event_type: Canonical event type string.
        payload: Strongly-typed payload of type ``T``.
    """

    event_type: str
    payload: T
