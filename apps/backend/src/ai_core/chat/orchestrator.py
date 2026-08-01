"""Chat Orchestrator — coordinates the full chat pipeline.

Pipeline:
  User Message → Context Manager → LLM Engine → Response → Persist
"""

from __future__ import annotations

import dataclasses
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

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
from src.ai_core.llm.models import LLMRequest, StreamingChunk
from src.ai_core.llm.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


_QUERY_REWRITE_PROMPT = (
    "Given the conversation history and a follow-up question, "
    "rewrite the question to be self-contained — a standalone version "
    "that includes all necessary context from the history.\n\n"
    "Conversation history:\n{history}\n\n"
    "Follow-up question: {question}\n\n"
    "Rewritten question:"
)

_SUMMARY_PROMPT = (
    "Summarize the key points, questions, and answers from this conversation "
    "for continuing the discussion. Be concise but preserve important details "
    "and document references.\n\n{history}\n\nSummary:"
)


@dataclasses.dataclass
class PipelineTrace:
    """Per-request stage-level timing breakdown."""

    request_id: str = ""
    user_id: str = ""
    session_id: str = ""
    prompt_version: str = ""
    prompt_hash: str = ""
    model: str = ""
    provider: str = ""
    cache_hit: bool = False

    rewrite_ms: float = 0.0
    retrieval_ms: float = 0.0
    context_ms: float = 0.0
    llm_ms: float = 0.0
    save_ms: float = 0.0
    total_ms: float = 0.0
    chunks_retrieved: int = 0
    chunks_cited: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    # Fine-grained retrieval timings (written by the retrieve closure)
    embed_ms: float = 0.0
    vector_search_ms: float = 0.0
    bm25_ms: float = 0.0
    cross_encoder_ms: float = 0.0
    mmr_ms: float = 0.0

    def log(self, query: str, model: str) -> None:
        """Log the trace breakdown as structured info."""
        logger.info(
            "[TRACE] request=%s user=%s session=%s prompt=%s model=%s "
            "total=%dms rewrite=%d retrieval=%d context=%d llm=%d save=%d "
            "embed=%d vec=%d bm25=%d ce=%d mmr=%d "
            "chunks=%d cited=%d tokens=%d+%d",
            self.request_id, self.user_id[:8], self.session_id[:8],
            self.prompt_version, model, int(self.total_ms),
            int(self.rewrite_ms), int(self.retrieval_ms), int(self.context_ms),
            int(self.llm_ms), int(self.save_ms),
            int(self.embed_ms), int(self.vector_search_ms), int(self.bm25_ms),
            int(self.cross_encoder_ms), int(self.mmr_ms),
            self.chunks_retrieved, self.chunks_cited,
            self.prompt_tokens, self.completion_tokens,
        )

    def persist(self) -> None:
        """Record this trace to the TraceStore (fire-and-forget)."""
        from src.ai_core.tracing.models import RequestTrace
        from src.ai_core.tracing.store import TraceStore

        try:
            trace = RequestTrace(
                request_id=self.request_id or None,
                user_id=self.user_id,
                session_id=self.session_id,
                prompt_version=self.prompt_version,
                prompt_hash=self.prompt_hash,
                model=self.model,
                provider=self.provider,
                cache_hit=self.cache_hit,
                rewrite_ms=self.rewrite_ms,
                embed_ms=self.embed_ms,
                vector_search_ms=self.vector_search_ms,
                bm25_ms=self.bm25_ms,
                cross_encoder_ms=self.cross_encoder_ms,
                mmr_ms=self.mmr_ms,
                context_ms=self.context_ms,
                llm_ms=self.llm_ms,
                save_ms=self.save_ms,
                total_ms=self.total_ms,
                chunks_retrieved=self.chunks_retrieved,
                chunks_cited=self.chunks_cited,
                prompt_tokens=self.prompt_tokens,
                completion_tokens=self.completion_tokens,
            )
            import asyncio

            asyncio.get_event_loop().create_task(TraceStore.record(trace))
        except Exception:
            logger.exception("Failed to persist request trace")

    def apply(self, source: Any) -> None:
        """Copy identity fields from an external RequestTrace if provided."""
        if source is None:
            return
        for attr in ("request_id", "user_id", "session_id", "prompt_version",
                     "prompt_hash", "model", "provider", "cache_hit",
                     "rewrite_ms", "context_ms", "chunks_retrieved", "chunks_cited",
                     "prompt_tokens", "completion_tokens"):
            val = getattr(source, attr, None)
            if val:
                setattr(self, attr, val)


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
        retrieve_chunks: Callable[[str, list[str], int, Any], Awaitable[list[ContextChunk]]] | None = None,
        request_trace: Any | None = None,
    ) -> tuple[ChatMessageModel, list[CitationReference]]:
        """Process a user message through the full pipeline.

        Args:
            session_id: The chat session ID.
            user_message: The user's message text.
            retrieve_chunks: Optional callable to retrieve chunks
                (query, report_ids, top_k) -> list[ContextChunk].
            request_trace: Optional RequestTrace to stamp with stage timings.

        Returns:
            (assistant_message, citations)
        """
        trace = PipelineTrace()
        trace.apply(request_trace)
        trace.session_id = session_id
        t0 = time.monotonic()

        # Validate
        self._validation.validate_message(user_message)

        # Load session
        session_model = await self._get_session_or_raise(session_id)
        session = self._model_to_session(session_model)

        # Save user message
        await self._create_user_message(session_id, user_message)

        # Load conversation history (includes the user message just saved)
        history = await self._load_history(session_id)

        # Query rewriting for multi-turn — make follow-ups self-contained
        search_query = user_message
        t_rewrite = time.monotonic()
        if len(history) >= 3 and session.summary:
            rewritten = await self._rewrite_query(user_message, session.summary)
            if rewritten:
                logger.debug("Rewrote query: %r -> %r", user_message[:50], rewritten[:50])
                search_query = rewritten
        trace.rewrite_ms = (time.monotonic() - t_rewrite) * 1000

        # Retrieve context chunks
        t_ret = time.monotonic()
        chunks: list[ContextChunk] = []
        if retrieve_chunks and session.report_ids:
            chunks = await retrieve_chunks(
                search_query, session.report_ids, self._config.retrieval_top_k, trace
            )
        trace.retrieval_ms = (time.monotonic() - t_ret) * 1000
        trace.chunks_retrieved = len(chunks)

        # Determine context strategy from session mode
        strategy = self._mode_to_strategy(session.mode)

        # Build context
        t_ctx = time.monotonic()
        context_config = ContextConfiguration(default_strategy=strategy)
        ctx = await self._context_pipeline.run(
            query=user_message,
            chunks=chunks,
            history=history,  # type: ignore[arg-type]
            config=context_config,
        )
        trace.context_ms = (time.monotonic() - t_ctx) * 1000

        # Build LLM request
        llm_request = self._prompt_builder.build(ctx)

        # Generate response
        t_llm = time.monotonic()
        response = await self._llm.generate(llm_request)
        trace.llm_ms = (time.monotonic() - t_llm) * 1000
        if response.metadata.token_usage:
            trace.prompt_tokens = response.metadata.token_usage.prompt_tokens
            trace.completion_tokens = response.metadata.token_usage.completion_tokens

        # Extract citations from context chunks
        citations = self._citations.extract(ctx.chunks, response.text)
        trace.chunks_cited = len(citations)

        # Save assistant message
        t_save = time.monotonic()
        assistant_msg = await self._create_assistant_message(session_id, response.text, citations)

        # Update session timestamp + summary
        all_history = await self._load_history(session_id)
        if len(all_history) >= 6:  # 3+ turns → generate/refresh summary
            summary = await self._generate_summary(session_id, all_history)
            if summary:
                await self._session_mgr.update_session(session_id, summary=summary)
        else:
            await self._session_mgr.update_session(session_id)
        trace.save_ms = (time.monotonic() - t_save) * 1000

        trace.total_ms = (time.monotonic() - t0) * 1000
        model = getattr(self._llm, '_config', None)
        model_name = model.model_name if model else "unknown"

        # Stamp identity from LLM request/response metadata
        req_meta = getattr(llm_request, "metadata", {}) or {}
        trace.prompt_version = trace.prompt_version or req_meta.get("prompt_version", "")
        trace.prompt_hash = trace.prompt_hash or req_meta.get("prompt_hash", "")
        resp_meta = getattr(response, "metadata", None)
        if resp_meta is not None:
            trace.model = getattr(resp_meta, "model", "") or model_name
            trace.provider = getattr(resp_meta, "provider", "") or getattr(
                self._llm, "provider_name", ""
            )

        trace.log(user_message, model_name)
        trace.persist()

        return assistant_msg, citations

    # ------------------------------------------------------------------
    # Streaming message handling
    # ------------------------------------------------------------------

    async def process_message_streaming(
        self,
        session_id: str,
        user_message: str,
        retrieve_chunks: Callable[[str, list[str], int, Any], Awaitable[list[ContextChunk]]] | None = None,
        request_trace: Any | None = None,
    ) -> AsyncIterator[StreamingChunk]:
        """Process a message and stream the response tokens."""
        trace = PipelineTrace()
        trace.apply(request_trace)
        trace.session_id = session_id
        t0 = time.monotonic()

        self._validation.validate_message(user_message)

        session_model = await self._get_session_or_raise(session_id)
        session = self._model_to_session(session_model)

        await self._create_user_message(session_id, user_message)

        # Retrieve + context (same as non-streaming)
        t_ret = time.monotonic()
        chunks: list[ContextChunk] = []
        if retrieve_chunks and session.report_ids:
            chunks = await retrieve_chunks(
                user_message, session.report_ids, self._config.retrieval_top_k, trace
            )
        trace.retrieval_ms = (time.monotonic() - t_ret) * 1000
        trace.chunks_retrieved = len(chunks)

        history = await self._load_history(session_id)
        strategy = self._mode_to_strategy(session.mode)

        t_ctx = time.monotonic()
        context_config = ContextConfiguration(default_strategy=strategy)
        ctx = await self._context_pipeline.run(
            query=user_message,
            chunks=chunks,
            history=history,  # type: ignore[arg-type]
            config=context_config,
        )
        trace.context_ms = (time.monotonic() - t_ctx) * 1000

        llm_request = self._prompt_builder.build(ctx)
        llm_request.stream = True

        # Stream tokens, collect full text for persistence
        full_text: list[str] = []
        citations: list[CitationReference] = []
        t_llm = time.monotonic()

        async for chunk in self._llm.generate_stream(llm_request):
            if chunk.text:
                full_text.append(chunk.text)
            if chunk.finish_reason:
                trace.llm_ms = (time.monotonic() - t_llm) * 1000
                citations = self._citations.extract(ctx.chunks)
                trace.chunks_cited = len(citations)
                # Persist BEFORE yielding the final chunk — the consumer
                # may close the generator immediately after the final yield,
                # skipping any code after this loop.
                response_text = "".join(full_text)
                await self._create_assistant_message(session_id, response_text, citations)

                # Refresh summary if enough history accumulated
                all_history = await self._load_history(session_id)
                if len(all_history) >= 6:
                    summary = await self._generate_summary(session_id, all_history)
                    if summary:
                        await self._session_mgr.update_session(session_id, summary=summary)
                    else:
                        await self._session_mgr.update_session(session_id)
                else:
                    await self._session_mgr.update_session(session_id)

                trace.total_ms = (time.monotonic() - t0) * 1000
                model = getattr(self._llm, '_config', None)
                model_name = model.model_name if model else "unknown"

                req_meta = getattr(llm_request, "metadata", {}) or {}
                trace.prompt_version = trace.prompt_version or req_meta.get("prompt_version", "")
                trace.prompt_hash = trace.prompt_hash or req_meta.get("prompt_hash", "")
                trace.model = trace.model or model_name
                trace.provider = trace.provider or getattr(self._llm, "provider_name", "")

                trace.log(user_message, model_name)
                trace.persist()

                yield chunk
                return
            yield chunk

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

    # ------------------------------------------------------------------
    # Query rewriting & summarization
    # ------------------------------------------------------------------

    async def _rewrite_query(self, question: str, summary: str | None) -> str | None:
        """Rewrite a follow-up question to be self-contained using conversation summary."""
        if not summary or not question:
            return None
        try:
            history_text = f"Conversation summary: {summary}"
            prompt = _QUERY_REWRITE_PROMPT.format(history=history_text, question=question)
            req = LLMRequest(
                user_prompt=prompt,
                temperature=0.1,
                max_tokens=256,
            )
            resp = await self._llm.generate(req)
            rewritten = resp.text.strip().strip('"\'')
            return rewritten if rewritten and rewritten != question else None
        except Exception:
            logger.debug("Query rewriting failed, using original", exc_info=True)
            return None

    async def _generate_summary(
        self,
        session_id: str,
        history: list[ChatMessageModel],
    ) -> str | None:
        """Generate an LLM-based conversation summary."""
        try:
            history_lines = []
            for msg in history[-10:]:  # last 10 messages
                role = "User" if msg.role == "user" else "Assistant"
                history_lines.append(f"{role}: {msg.content[:300]}")
            history_text = "\n".join(history_lines)

            req = LLMRequest(
                user_prompt=_SUMMARY_PROMPT.format(history=history_text),
                temperature=0.2,
                max_tokens=512,
            )
            resp = await self._llm.generate(req)
            summary = resp.text.strip()
            return summary if summary else None
        except Exception:
            logger.debug("Summary generation failed", exc_info=True)
            return None

    @staticmethod
    def _model_to_session(model: ChatSessionModel) -> ChatSession:
        return ChatSession(
            id=model.id,
            title=model.title,
            report_ids=list(model.report_ids) if model.report_ids else [],
            mode=model.mode,
            summary=model.summary,
            created_at=model.created_at,
            updated_at=model.updated_at,
            archived=model.archived,
        )
