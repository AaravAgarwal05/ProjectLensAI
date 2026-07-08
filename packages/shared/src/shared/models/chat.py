"""Pydantic models for chat, conversation, and thread entities."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field
from pydantic.main import BaseModel


class Message(BaseModel):
    """A single message within a conversation.

    Attributes:
        id: Unique message identifier.
        conversation_id: Identifier of the parent conversation.
        role: Message role (e.g. ``"user"``, ``"assistant"``, ``"system"``).
        content: Text content of the message.
        metadata: Arbitrary metadata key-value pairs.
        created_at: Timestamp of creation.
    """

    model_config = {"frozen": True}

    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    role: str
    content: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime


class Conversation(BaseModel):
    """A conversation (chat session) between a user and the system.

    Attributes:
        id: Unique conversation identifier.
        title: Human-readable conversation title.
        user_id: Optional identifier of the owning user.
        messages: Ordered list of messages in the conversation.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
    """

    model_config = {"frozen": True}

    id: UUID = Field(default_factory=uuid4)
    title: str
    user_id: UUID | None = None
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class Thread(BaseModel):
    """A thread branching from a specific parent message.

    Attributes:
        id: Unique thread identifier.
        parent_message_id: Identifier of the message this thread branches from.
        messages: Ordered list of messages in the thread.
        created_at: Timestamp of creation.
    """

    id: UUID = Field(default_factory=uuid4)
    parent_message_id: UUID
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime
