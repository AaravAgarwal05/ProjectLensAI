"""API schemas for chat message and conversation operations."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field
from pydantic.main import BaseModel

from shared.models.analysis import Citation
from shared.models.chat import Message


class MessageCreate(BaseModel):
    """Request schema for creating a new message.

    Attributes:
        conversation_id: Optional conversation to attach the message to. If
            omitted a new conversation may be created server-side.
        role: Message role (defaults to ``"user"``).
        content: Text content of the message.
        metadata: Arbitrary metadata key-value pairs.
    """

    conversation_id: UUID | None = None
    role: str = "user"
    content: str
    metadata: dict = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Request schema for a chat completion.

    Attributes:
        message: The user's input message.
        conversation_id: Optional existing conversation identifier.
        stream: Whether to stream the response tokens.
    """

    message: str
    conversation_id: UUID | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Response schema for a chat completion.

    Attributes:
        message: The assistant's response message.
        conversation_id: Identifier of the conversation (new or existing).
        sources: List of supporting citations.
    """

    message: Message
    conversation_id: UUID
    sources: list[Citation] = Field(default_factory=list)
