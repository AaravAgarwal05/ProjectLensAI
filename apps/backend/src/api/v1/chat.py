"""Chat / conversation API endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai_core.chat.message_manager import MessageManager
from src.ai_core.chat.models import CitationReference
from src.ai_core.chat.session_manager import SessionManager
from src.api.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class CitationRefOut(BaseModel):
    """Citation reference in API responses."""

    report_id: str = ""
    report_title: str = ""
    page_number: int | None = None
    section_name: str = ""
    chunk_id: str = ""
    score: float = 0.0


class MessageOut(BaseModel):
    """A single chat message in API responses."""

    id: str
    role: str
    content: str
    citations: list[CitationRefOut] = Field(default_factory=list)
    created_at: str


class SessionOut(BaseModel):
    """Chat session in API responses."""

    id: str
    title: str
    report_ids: list[str] = Field(default_factory=list)
    mode: str = "single"
    message_count: int = 0
    created_at: str
    updated_at: str
    archived: bool = False


class CreateSessionRequest(BaseModel):
    """Request to create a new chat session."""

    title: str = "New Chat"
    report_ids: list[str] = Field(default_factory=list)
    mode: str = "single"


class SendMessageRequest(BaseModel):
    """Request to send a chat message."""

    message: str
    session_id: str | None = None
    report_ids: list[str] | None = None
    mode: str = "single"


class SendMessageResponse(BaseModel):
    """Response after processing a chat message."""

    session_id: str
    message: MessageOut
    citations: list[CitationRefOut] = Field(default_factory=list)


class UpdateSessionRequest(BaseModel):
    """Request to update a chat session."""

    title: str | None = None
    mode: str | None = None
    report_ids: list[str] | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _model_to_session_out(
    session_model: Any,
    message_count: int = 0,
) -> SessionOut:
    """Convert a ChatSessionModel to SessionOut."""
    return SessionOut(
        id=session_model.id,
        title=session_model.title,
        report_ids=list(session_model.report_ids) if session_model.report_ids else [],
        mode=session_model.mode,
        message_count=message_count,
        created_at=session_model.created_at.isoformat() if session_model.created_at else "",
        updated_at=session_model.updated_at.isoformat() if session_model.updated_at else "",
        archived=session_model.archived,
    )


def _model_to_message_out(message_model: Any) -> MessageOut:
    """Convert a ChatMessageModel to MessageOut."""
    citations = []
    if hasattr(message_model, "citations") and message_model.citations:
        for c in message_model.citations:
            if isinstance(c, dict):
                citations.append(CitationRefOut(**c))
            elif isinstance(c, CitationReference):
                citations.append(CitationRefOut(**c.__dict__))
    return MessageOut(
        id=message_model.id,
        role=message_model.role,
        content=message_model.content,
        citations=citations,
        created_at=message_model.created_at.isoformat() if message_model.created_at else "",
    )


# ---------------------------------------------------------------------------
# Session endpoints
# ---------------------------------------------------------------------------


@router.get("/conversations", response_model=list[SessionOut])
async def list_conversations(
    include_archived: bool = Query(False, alias="include_archived"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[SessionOut]:
    """List all chat sessions."""
    session_mgr = SessionManager(db)
    sessions = await session_mgr.list_sessions(
        include_archived=include_archived,
        limit=limit,
        offset=offset,
    )
    result: list[SessionOut] = []
    msg_mgr = MessageManager(db)
    for s in sessions:
        count = await msg_mgr.count_messages(s.id)
        result.append(_model_to_session_out(s, message_count=count))
    return result


@router.post("/conversations", response_model=SessionOut, status_code=201)
async def create_conversation(
    body: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    """Create a new chat session."""
    session_mgr = SessionManager(db)
    session = await session_mgr.create_session(
        title=body.title,
        report_ids=body.report_ids,
        mode=body.mode,
    )
    return _model_to_session_out(session)


@router.get("/conversations/{session_id}", response_model=SessionOut)
async def get_conversation(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    """Get a chat session by ID."""
    session_mgr = SessionManager(db)
    session = await session_mgr.get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )
    msg_mgr = MessageManager(db)
    count = await msg_mgr.count_messages(session_id)
    return _model_to_session_out(session, message_count=count)


@router.patch("/conversations/{session_id}", response_model=SessionOut)
async def update_conversation(
    session_id: str,
    body: UpdateSessionRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    """Update a chat session (title, mode, report_ids)."""
    session_mgr = SessionManager(db)
    updates: dict[str, Any] = {}
    if body.title is not None:
        updates["title"] = body.title
    if body.mode is not None:
        updates["mode"] = body.mode
    if body.report_ids is not None:
        updates["report_ids"] = body.report_ids

    updated = await session_mgr.update_session(session_id, **updates)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    msg_mgr = MessageManager(db)
    count = await msg_mgr.count_messages(session_id)
    return _model_to_session_out(updated, message_count=count)


@router.delete("/conversations/{session_id}", status_code=204)
async def delete_conversation(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a chat session and all its messages."""
    session_mgr = SessionManager(db)
    deleted = await session_mgr.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")


@router.post("/conversations/{session_id}/archive", response_model=SessionOut)
async def archive_conversation(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    """Archive a chat session."""
    session_mgr = SessionManager(db)
    session = await session_mgr.archive_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    msg_mgr = MessageManager(db)
    count = await msg_mgr.count_messages(session_id)
    return _model_to_session_out(session, message_count=count)


@router.post("/conversations/{session_id}/restore", response_model=SessionOut)
async def restore_conversation(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> SessionOut:
    """Restore an archived chat session."""
    session_mgr = SessionManager(db)
    session = await session_mgr.restore_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    msg_mgr = MessageManager(db)
    count = await msg_mgr.count_messages(session_id)
    return _model_to_session_out(session, message_count=count)


# ---------------------------------------------------------------------------
# Message endpoints
# ---------------------------------------------------------------------------


@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
) -> SendMessageResponse:
    """Send a message and get an AI response (non-streaming).

    If session_id is not provided, a new session is created automatically.
    The response is returned as a complete JSON payload.
    """
    session_mgr = SessionManager(db)
    msg_mgr = MessageManager(db)

    # Resolve / create session
    session_id = body.session_id
    if session_id is None:
        session = await session_mgr.create_session(
            title=body.message[:80] if body.message else "New Chat",
            report_ids=body.report_ids or [],
            mode=body.mode,
        )
        session_id = session.id
    else:
        session = await session_mgr.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    # Save user message
    await msg_mgr.create_message(
        session_id=session_id,
        role="user",
        content=body.message,
    )

    # Generate AI response
    ai_content = _generate_placeholder_response(body.message)
    assistant_msg = await msg_mgr.create_message(
        session_id=session_id,
        role="assistant",
        content=ai_content,
    )

    # Update session timestamp
    await session_mgr.update_session(session_id)

    # Return

    return SendMessageResponse(
        session_id=session_id,
        message=_model_to_message_out(assistant_msg),
        citations=[],
    )


@router.get("/conversations/{session_id}/messages", response_model=list[MessageOut])
async def list_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    before_id: str | None = Query(None, alias="before_id"),
    db: AsyncSession = Depends(get_db),
) -> list[MessageOut]:
    """List messages in a session."""
    session_mgr = SessionManager(db)
    session = await session_mgr.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    msg_mgr = MessageManager(db)
    msgs = await msg_mgr.list_messages(
        session_id=session_id,
        limit=limit,
        offset=offset,
        before_id=before_id,
    )
    return [_model_to_message_out(m) for m in msgs]


@router.delete(
    "/conversations/{session_id}/messages/{message_id}",
    status_code=204,
)
async def delete_message(
    session_id: str,
    message_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a single message."""
    msg_mgr = MessageManager(db)
    deleted = await msg_mgr.delete_message(message_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Message '{message_id}' not found")


# ---------------------------------------------------------------------------
# Placeholder helpers
# ---------------------------------------------------------------------------


def _generate_placeholder_response(message: str) -> str:
    """Generate a placeholder AI response.

    TODO: Replace with actual LLM orchestration when the full
    chat pipeline is wired into the app bootstrap.
    """
    message_lower = message.lower()
    if "hello" in message_lower or "hi" in message_lower:
        return (
            "Hello! I'm the ProjectLens AI assistant. "
            "You can ask me questions about your documents."
        )
    if "report" in message_lower or "document" in message_lower:
        return "I can help you analyze your reports and documents. What would you like to know?"
    return (
        f"I received your message: '{message[:100]}'. The full AI pipeline will be connected soon."
    )
