"""Chat Orchestrator — coordinates the full chat pipeline.

Pipeline:
  User Message → Context Manager → LLM Engine → Response → Persist
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator, Callable

from src.ai_core.chat.citations import CitationEngine
from src.ai_core.chat.config import ChatConfiguration
from src.ai_core.chat.database import ChatMessageModel, ChatSessionModel
from src.ai_core.chat.message_manager import MessageManager
from src.ai_core.chat.models import (
    ChatSession,
    CitationReference,
    MessageRole,
)
from src.ai_core.chat.session_manager import SessionManager
from src.ai_core.chat.validation import ChatValidationEngine
from src.ai_core.context.configuration import ContextConfiguration
from src.ai_core.context.models import ContextChunk
from src.ai_core.context.pipeline import ContextAssemblyPipeline
from src.ai_core.llm.base import LLMProvider
from src.ai_core.llm.models import StreamingChunk
from src.ai_core.llm.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class ChatOrchestrator:
    """Coordinates the full chat pipeline.

    The orchestrator does NOT implement retrieval, embedding, or
    vector-store logic itself — it delegates to provided components.
    """

    def __init__(
        self,
        session_manager: SessionManager,
        message_manager: MessageManager,
        citation_engine: CitationEngine,
        context_pipeline: ContextAssemblyPipeline,
        prompt_builder: PromptBuilder,
        llm_provider: LLMProvider,
        config: ChatConfiguration | None = None,
        validation_engine: ChatValidationEngine | None = None,
    ) -> None:
        self._session_mgr = session_manager
        self._message_mgr = message_manager
        self._citations = citation_engine
        self._context_pipeline = context_pipeline
        self._prompt_builder = prompt_builder
        self._llm = llm_provider
        self._config = config or ChatConfiguration()
        self._validation = validation_engine or ChatValidationEngine()

    # ------------------------------------------------------------------
    # Non-streaming message handling
    # ------------------------------------------------------------------

    async def process_message(
        self,
        session_id: str,
        user_message: str,
        retrieve_chunks: Callable[[str, list[str], int], list[ContextChunk]] | None = None,
    ) -> tuple[ChatMessageModel, list[CitationReference]]:
        """Process a user message through the full pipeline.

        Args:
            session_id: The chat session ID.
            user_message: The user's message text.
            retrieve_chunks: Optional callable to retrieve chunks
                (query, report_ids, top_k) -> list[ContextChunk].

        Returns:
            (assistant_message, citations)
        """
        # Validate
        self._validation.validate_message(user_message)

        # Load session
        session_model = await self._get_session_or_raise(session_id)
        session = self._model_to_session(session_model)

        # Save user message
        await self._create_user_message(session_id, user_message)

        # Retrieve context chunks
        chunks: list[ContextChunk] = []
        if retrieve_chunks and session.report_ids:
            chunks = retrieve_chunks(user_message, session.report_ids, self._config.retrieval_top_k)

        # Load conversation history
        history = await self._load_history(session_id)

        # Determine context strategy from session mode
        strategy = self._mode_to_strategy(session.mode)

        # Build context
        context_config = ContextConfiguration(default_strategy=strategy)
        ctx = await self._context_pipeline.run(
            query=user_message,
            chunks=chunks,
            history=history,  # type: ignore[arg-type]
            config=context_config,
        )

        # Build LLM request
        llm_request = self._prompt_builder.build(ctx)

        # Generate response
        start = time.monotonic()
        response = await self._llm.generate(llm_request)
        _ = (time.monotonic() - start) * 1000  # latency placeholder

        # Extract citations from context chunks
        citations = self._citations.extract(ctx.chunks, response.text)

        # Save assistant message
        assistant_msg = await self._create_assistant_message(session_id, response.text, citations)

        # Update session timestamp
        await self._session_mgr.update_session(session_id)

        return assistant_msg, citations

    # ------------------------------------------------------------------
    # Streaming message handling
    # ------------------------------------------------------------------

    async def process_message_streaming(
        self,
        session_id: str,
        user_message: str,
        retrieve_chunks: Callable[[str, list[str], int], list[ContextChunk]] | None = None,
    ) -> AsyncIterator[StreamingChunk]:
        """Process a message and stream the response tokens.

        Args:
            session_id: The chat session ID.
            user_message: The user's message text.
            retrieve_chunks: Optional callable to retrieve chunks.

        Yields:
            StreamingChunks as tokens arrive.
        """
        self._validation.validate_message(user_message)

        session_model = await self._get_session_or_raise(session_id)
        session = self._model_to_session(session_model)

        await self._create_user_message(session_id, user_message)

        # Retrieve + context (same as non-streaming)
        chunks: list[ContextChunk] = []
        if retrieve_chunks and session.report_ids:
            chunks = retrieve_chunks(user_message, session.report_ids, self._config.retrieval_top_k)

        history = await self._load_history(session_id)
        strategy = self._mode_to_strategy(session.mode)

        context_config = ContextConfiguration(default_strategy=strategy)
        ctx = await self._context_pipeline.run(
            query=user_message,
            chunks=chunks,
            history=history,  # type: ignore[arg-type]
            config=context_config,
        )

        llm_request = self._prompt_builder.build(ctx)
        llm_request.stream = True

        # Stream tokens, collect full text for persistence
        full_text: list[str] = []
        citations: list[CitationReference] = []

        async for chunk in self._llm.generate_stream(llm_request):
            if chunk.text:
                full_text.append(chunk.text)
            if chunk.finish_reason:
                # Extract citations from the (now final) context
                citations = self._citations.extract(ctx.chunks)
                yield chunk
                break
            yield chunk

        # Persist the assistant message
        response_text = "".join(full_text)
        await self._create_assistant_message(session_id, response_text, citations)
        await self._session_mgr.update_session(session_id)

    # ------------------------------------------------------------------
    # Mode mapping
    # ------------------------------------------------------------------

    def _mode_to_strategy(self, mode: str) -> str:
        mapping = {
            "single": "single_document",
            "multi": "multi_document",
            "comparison": "comparison",
        }
        return mapping.get(mode, "single_document")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_session_or_raise(self, session_id: str) -> ChatSessionModel:
        session = await self._session_mgr.get_session(session_id)
        if session is None:
            from src.ai_core.chat.exceptions import SessionNotFoundError

            raise SessionNotFoundError(f"Session '{session_id}' not found")
        return session

    async def _create_user_message(self, session_id: str, content: str) -> ChatMessageModel:
        return await self._message_mgr.create_message(
            session_id=session_id,
            role=MessageRole.USER.value,
            content=content,
        )

    async def _create_assistant_message(
        self,
        session_id: str,
        content: str,
        citations: list[CitationReference] | None = None,
    ) -> ChatMessageModel:
        citation_dicts = self._citations.to_dicts(citations or [])
        return await self._message_mgr.create_message(
            session_id=session_id,
            role=MessageRole.ASSISTANT.value,
            content=content,
            citations=citation_dicts,
        )

    async def _load_history(self, session_id: str) -> list[ChatMessageModel]:
        msgs = await self._message_mgr.list_messages(
            session_id, limit=self._config.max_history_messages
        )
        return msgs

    @staticmethod
    def _model_to_session(model: ChatSessionModel) -> ChatSession:
        return ChatSession(
            id=model.id,
            title=model.title,
            report_ids=list(model.report_ids) if model.report_ids else [],
            mode=model.mode,
            created_at=model.created_at,
            updated_at=model.updated_at,
            archived=model.archived,
        )
