"""Chat / conversation API endpoints."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Awaitable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai_core.chat.citations import CitationEngine
from src.ai_core.chat.config import ChatConfiguration
from src.ai_core.chat.message_manager import MessageManager
from src.ai_core.chat.models import CitationReference
from src.ai_core.chat.orchestrator import ChatOrchestrator
from src.ai_core.chat.session_manager import SessionManager
from src.ai_core.chat.validation import ChatValidationEngine
from src.ai_core.context.models import ContextChunk
from src.ai_core.context.pipeline import ContextAssemblyPipeline
from src.ai_core.context.strategies.single_document import SingleDocumentStrategy
from src.ai_core.llm.configuration import LLMConfiguration
from src.ai_core.llm.prompt_builder import PromptBuilder
from src.ai_core.llm.providers.ollama import OllamaProvider
from src.api.dependencies import get_current_user, get_db
from src.api.rate_limiter import limiter
from src.database.models import User
from src.services.rag_chat_service import RAGChatService

logger = logging.getLogger(__name__)

router = APIRouter()

# Singleton RAG service instance — lazy-init so it doesn't block import time.
_rag_service: RAGChatService | None = None
_chroma_client: Any | None = None


def _get_chroma_client() -> Any:
    global _chroma_client  # noqa: PLW0603
    if _chroma_client is None:
        import chromadb

        from src.config.settings import get_settings

        s = get_settings()
        _chroma_client = chromadb.HttpClient(host=s.CHROMA_HOST, port=s.CHROMA_PORT)
    return _chroma_client


def _get_rag_service() -> RAGChatService:
    global _rag_service  # noqa: PLW0603
    if _rag_service is None:
        _rag_service = RAGChatService()
    return _rag_service


# ---------------------------------------------------------------------------
# Orchestrator + chunk retrieval helpers
# ---------------------------------------------------------------------------


def _build_orchestrator(
    db: AsyncSession,
    mode: str = "single",
    model_name: str | None = None,
) -> ChatOrchestrator | None:
    """Build a ChatOrchestrator with default wiring.

    Args:
        db: Database session.
        mode: Chat mode (single, multi, comparison).
        model_name: Optional model override. Uses LLMConfiguration default if None.

    Returns ``None`` if the LLM provider is unavailable (the caller
    should fall back to a placeholder response).
    """
    try:
        from src.config.settings import get_settings

        _s = get_settings()
        llm_config = (
            LLMConfiguration(model_name=model_name, base_url=_s.ollama_base_url)
            if model_name
            else LLMConfiguration(base_url=_s.ollama_base_url)
        )
        llm_provider = OllamaProvider(config=llm_config)
        prompt_builder = PromptBuilder(config=llm_config)
        citation_engine = CitationEngine()
        validation_engine = ChatValidationEngine()

        strategy = SingleDocumentStrategy()
        context_pipeline = ContextAssemblyPipeline(strategy=strategy)

        chat_config = ChatConfiguration(
            default_mode=mode,
        )

        return ChatOrchestrator(
            session_manager=SessionManager(db),
            message_manager=MessageManager(db),
            citation_engine=citation_engine,
            context_pipeline=context_pipeline,
            prompt_builder=prompt_builder,
            llm_provider=llm_provider,
            config=chat_config,
            validation_engine=validation_engine,
        )
    except Exception:
        logger.exception("Failed to build ChatOrchestrator")
        return None


def _build_retrieve_chunks() -> (
    callable[[str, list[str], int], Awaitable[list[ContextChunk]]] | None
):
    """Build an async callable that embeds a query and retrieves ContextChunks from ChromaDB.

    Returns ``None`` if ChromaDB is not available.
    """
    try:
        from src.config.settings import get_settings

        _s = get_settings()
        chroma_host = _s.CHROMA_HOST
        chroma_port = _s.CHROMA_PORT
        chroma_client = _get_chroma_client()

        async def retrieve(query: str, report_ids: list[str], top_k: int) -> list[ContextChunk]:
            """Embed *query*, search each report collection, return ContextChunks."""
            from src.services.rag_chat_service import RAGChatService

            rag = RAGChatService(chroma_host=chroma_host, chroma_port=chroma_port, top_k=top_k)
            query_vec = await rag._embed_with_cache(query)  # noqa: SLF001

            all_chunks: list[ContextChunk] = []
            for rid in report_ids:
                try:
                    collection = chroma_client.get_collection(name=f"report_{rid}")
                except Exception:
                    logger.info("No ChromaDB collection for report %s, skipping", rid)
                    continue

                results = collection.query(
                    query_embeddings=[query_vec],
                    n_results=top_k,
                    include=["metadatas", "distances", "documents"],
                )

                ids = results.get("ids", [[]])[0]
                distances = results.get("distances", [[]])[0]
                documents = results.get("documents", [[]])[0]
                metadatas = results.get("metadatas", [[]])[0]

                for i in range(len(ids)):
                    score = 1.0 - distances[i] if distances and i < len(distances) else 0.0
                    meta = metadatas[i] if metadatas and i < len(metadatas) else {}
                    all_chunks.append(
                        ContextChunk(
                            chunk_id=ids[i],
                            content=documents[i] if documents and i < len(documents) else "",
                            score=score,
                            source_id=rid,
                            source_title=meta.get("title", "") or "",
                            page_number=meta.get("page_number"),
                            section_name=meta.get("section_name", "") or "",
                        )
                    )

            all_chunks.sort(key=lambda c: c.score, reverse=True)
            return all_chunks

        return retrieve
    except Exception:
        logger.warning("ChromaDB not available for chunk retrieval", exc_info=True)
        return None


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
    user: User = Depends(get_current_user),
) -> list[SessionOut]:
    """List all chat sessions for the current user."""
    session_mgr = SessionManager(db)
    sessions = await session_mgr.list_sessions(
        include_archived=include_archived,
        limit=limit,
        offset=offset,
        user_id=str(user.id),
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
    user: User = Depends(get_current_user),
) -> SessionOut:
    """Create a new chat session."""
    session_mgr = SessionManager(db)
    session = await session_mgr.create_session(
        title=body.title,
        report_ids=body.report_ids,
        mode=body.mode,
        user_id=str(user.id),
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
@limiter.limit("30/minute")
async def send_message(
    request: Request,
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
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
            user_id=str(user.id),
        )
        session_id = session.id
    else:
        session = await session_mgr.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    # Generate AI response — use RAG if report_ids are provided, else placeholder
    # Note: user message is saved inside each branch (orchestrator saves it internally)
    report_ids = body.report_ids or []
    citations_out: list[CitationRefOut] = []

    if report_ids:
        user_prefs = user.preferences or {}
        user_model = user_prefs.get("llm_model") if isinstance(user_prefs, dict) else None
        orchestrator = _build_orchestrator(db, mode=body.mode, model_name=user_model)
        retrieve_chunks = _build_retrieve_chunks()
        use_orchestrator = orchestrator is not None and retrieve_chunks is not None

        if use_orchestrator:
            # Orchestrator handles persistence internally — skip manual save
            async def _retrieve_and_budget(
                query: str,
                rids: list[str],
                top_k: int,
            ) -> list[ContextChunk]:
                assert retrieve_chunks is not None  # noqa: S101
                return await retrieve_chunks(query, rids, top_k)

            try:
                assistant_msg_model, citation_refs = await orchestrator.process_message(
                    session_id=session_id,
                    user_message=body.message,
                    retrieve_chunks=_retrieve_and_budget,
                )
                citations_out = [
                    CitationRefOut(
                        report_id=c.report_id,
                        report_title=c.report_title,
                        page_number=c.page_number,
                        section_name=c.section_name,
                        chunk_id=c.chunk_id,
                        score=c.score,
                    )
                    for c in citation_refs
                ]
                assistant_msg = assistant_msg_model
            except Exception:
                logger.exception("Orchestrator failed, falling back to RAGChatService")
                use_orchestrator = False

        if not use_orchestrator:
            # Save user message (orchestrator didn't, or we fell back)
            await msg_mgr.create_message(
                session_id=session_id,
                role="user",
                content=body.message,
            )
            rag = _get_rag_service()
            ai_content, raw_citations = await rag.answer(body.message, report_ids)
            citations_out = [CitationRefOut(**c) for c in raw_citations]
            assistant_msg = await msg_mgr.create_message(
                session_id=session_id,
                role="assistant",
                content=ai_content,
                citations=[c.model_dump() for c in citations_out],
            )
    else:
        ai_content = _generate_placeholder_response(body.message)
        assistant_msg = await msg_mgr.create_message(
            session_id=session_id,
            role="assistant",
            content=ai_content,
        )

    # Update session timestamp
    await session_mgr.update_session(session_id)

    return SendMessageResponse(
        session_id=session_id,
        message=_model_to_message_out(assistant_msg),
        citations=citations_out,
    )


# ---------------------------------------------------------------------------
# SSE streaming endpoint
# ---------------------------------------------------------------------------


async def _stream_events(
    session_id: str,
    message: str,
    report_ids: list[str],
    db: AsyncSession,
    mode: str = "single",
    model_name: str | None = None,
) -> AsyncIterator[str]:
    """Stream SSE events for a chat message."""
    orchestrator = _build_orchestrator(db, mode=mode, model_name=model_name)
    retrieve_chunks = _build_retrieve_chunks()

    if orchestrator is None or retrieve_chunks is None:
        yield f"data: {json.dumps({'type': 'error', 'message': 'AI engine not available'})}\n\n"
        return

    async def _retrieve_and_budget(
        query: str,
        rids: list[str],
        top_k: int,
    ) -> list[ContextChunk]:
        assert retrieve_chunks is not None  # noqa: S101
        return await retrieve_chunks(query, rids, top_k)

    try:
        full_text: list[str] = []
        async for chunk in orchestrator.process_message_streaming(
            session_id=session_id,
            user_message=message,
            retrieve_chunks=_retrieve_and_budget,
        ):
            if chunk.text:
                full_text.append(chunk.text)
                yield f"data: {json.dumps({'type': 'token', 'text': chunk.text})}\n\n"
            if chunk.finish_reason:
                # Done — yield final event with citations
                yield (
                    f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"
                )
                return
    except Exception as exc:
        logger.exception("Streaming failed")
        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"


@router.post("/send/stream")
@limiter.limit("30/minute")
async def send_message_stream(
    request: Request,
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Send a message and stream the AI response via SSE."""
    session_mgr = SessionManager(db)

    # Resolve / create session
    session_id = body.session_id
    if session_id is None:
        session = await session_mgr.create_session(
            title=body.message[:80] if body.message else "New Chat",
            report_ids=body.report_ids or [],
            mode=body.mode,
            user_id=str(user.id),
        )
        session_id = session.id
    else:
        session = await session_mgr.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    return StreamingResponse(
        _stream_events(
            session_id=session_id,
            message=body.message,
            report_ids=body.report_ids or [],
            db=db,
            mode=body.mode,
            model_name=user.preferences.get("llm_model") if isinstance(user.preferences, dict) else None,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
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
