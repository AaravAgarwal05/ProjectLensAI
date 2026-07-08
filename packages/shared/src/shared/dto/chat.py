"""Data transfer objects for chat context propagation."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field
from pydantic.main import BaseModel


class ChatContextDTO(BaseModel):
    """DTO carrying contextual data for a chat interaction.

    Attributes:
        conversation_id: Optional identifier of the active conversation.
        relevant_chunks: List of relevant document chunk contents or references.
        system_prompt: Optional system-level prompt override.
    """

    conversation_id: UUID | None = None
    relevant_chunks: list = Field(default_factory=list)
    system_prompt: str | None = None
