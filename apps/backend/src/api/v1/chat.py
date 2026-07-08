"""Chat / conversation endpoints."""


from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.dependencies import get_settings
from src.config.settings import AppSettings

router = APIRouter()


class ChatMessage(BaseModel):
    """A single chat message."""

    role: str
    content: str


class ChatRequest(BaseModel):
    """Request payload for sending a chat message."""

    conversation_id: str | None = None
    message: str
    document_ids: list[str] | None = None


class ChatResponse(BaseModel):
    """Response returned after processing a chat message."""

    conversation_id: str
    reply: str


class ConversationSummary(BaseModel):
    """Lightweight summary of a conversation."""

    id: str
    title: str
    created_at: str
    message_count: int


@router.post("", response_model=ChatResponse)
async def send_message(
    body: ChatRequest,
    settings: AppSettings = Depends(get_settings),
) -> ChatResponse:
    """Send a chat message and receive an AI-generated reply.

    This is a placeholder — full implementation will follow.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Chat not yet implemented",
    )


@router.get("/conversations")
async def list_conversations(
    settings: AppSettings = Depends(get_settings),
) -> list[ConversationSummary]:
    """List all conversations for the current user.

    This is a placeholder — full implementation will follow.
    """
    return []
