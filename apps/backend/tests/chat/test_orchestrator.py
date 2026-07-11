"""Tests for ChatOrchestrator."""

from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.ai_core.chat.exceptions import SessionNotFoundError
from src.ai_core.chat.orchestrator import ChatOrchestrator
from src.ai_core.context.models import ContextChunk, LLMContext
from src.ai_core.llm.models import LLMRequest, LLMResponse, StreamingChunk

pytest_plugins = ["tests.chat.fixtures"]


@pytest.fixture
def mock_context_pipeline():
    """Create a mocked ContextAssemblyPipeline."""
    pipeline = MagicMock()
    ctx = LLMContext(
        query="test query",
        chunks=[
            ContextChunk(
                chunk_id="c1",
                content="Test content",
                score=0.95,
                source_id="r1",
                source_title="Report 1",
            )
        ],
        conversation_history=[],
    )
    pipeline.run = AsyncMock(return_value=ctx)
    return pipeline


@pytest.fixture
def mock_prompt_builder():
    """Create a mocked PromptBuilder."""
    builder = MagicMock()
    builder.build.return_value = LLMRequest(
        user_prompt="test prompt",
        system_prompt="test system prompt",
        temperature=0.7,
        max_tokens=2048,
    )
    return builder


@pytest.fixture
def mock_llm_provider():
    """Create a mocked LLMProvider."""
    provider = MagicMock()
    provider.generate = AsyncMock(return_value=LLMResponse(text="Test response from LLM"))
    return provider


@pytest.fixture
def mock_retrieve_chunks():
    """Create a mock retrieval callable."""
    return MagicMock(
        return_value=[
            ContextChunk(
                chunk_id="retrieved-1",
                content="Retrieved content",
                score=0.9,
                source_id="r1",
                source_title="Report 1",
            )
        ]
    )


@pytest.fixture
def orchestrator(
    session_manager,
    message_manager,
    citation_engine,
    mock_context_pipeline,
    mock_prompt_builder,
    mock_llm_provider,
):
    """Create a ChatOrchestrator with mocked dependencies."""
    return ChatOrchestrator(
        session_manager=session_manager,
        message_manager=message_manager,
        citation_engine=citation_engine,
        context_pipeline=mock_context_pipeline,
        prompt_builder=mock_prompt_builder,
        llm_provider=mock_llm_provider,
    )


class TestChatOrchestrator:
    @pytest.mark.asyncio
    async def test_process_message_basic(
        self,
        orchestrator: ChatOrchestrator,
        session_manager,
    ):
        session = await session_manager.create_session(title="Test", report_ids=["r1"])
        assistant_msg, citations = await orchestrator.process_message(
            session_id=session.id,
            user_message="Hello",
        )
        assert assistant_msg is not None
        assert assistant_msg.role == "assistant"
        assert assistant_msg.content == "Test response from LLM"

    @pytest.mark.asyncio
    async def test_process_message_with_retrieval(
        self,
        orchestrator: ChatOrchestrator,
        session_manager,
        mock_retrieve_chunks,
    ):
        session = await session_manager.create_session(title="Test", report_ids=["r1"])
        assistant_msg, citations = await orchestrator.process_message(
            session_id=session.id,
            user_message="Query about report",
            retrieve_chunks=mock_retrieve_chunks,
        )
        assert assistant_msg is not None
        assert assistant_msg.role == "assistant"
        mock_retrieve_chunks.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_saves_user_message(
        self,
        orchestrator: ChatOrchestrator,
        session_manager,
        message_manager,
    ):
        session = await session_manager.create_session(report_ids=["r1"])
        await orchestrator.process_message(session_id=session.id, user_message="Hello")
        # Verify user message persisted
        msgs = await message_manager.list_messages(session.id)
        assert len(msgs) >= 1
        user_msgs = [m for m in msgs if m.role == "user"]
        assert any(m.content == "Hello" for m in user_msgs)

    @pytest.mark.asyncio
    async def test_process_message_saves_assistant_message(
        self,
        orchestrator: ChatOrchestrator,
        session_manager,
        message_manager,
    ):
        session = await session_manager.create_session(report_ids=["r1"])
        await orchestrator.process_message(session_id=session.id, user_message="Hello")
        msgs = await message_manager.list_messages(session.id)
        assistant_msgs = [m for m in msgs if m.role == "assistant"]
        assert len(assistant_msgs) >= 1
        assert assistant_msgs[-1].content == "Test response from LLM"

    @pytest.mark.asyncio
    async def test_process_message_session_not_found(self, orchestrator: ChatOrchestrator):
        with pytest.raises(SessionNotFoundError):
            await orchestrator.process_message(session_id="nonexistent", user_message="Hello")

    @pytest.mark.asyncio
    async def test_process_message_empty_message(
        self, orchestrator: ChatOrchestrator, session_manager
    ):
        session = await session_manager.create_session()
        from src.ai_core.chat.exceptions import EmptyMessageError

        with pytest.raises(EmptyMessageError):
            await orchestrator.process_message(session_id=session.id, user_message="")

    @pytest.mark.asyncio
    async def test_process_message_no_report_ids(
        self,
        orchestrator: ChatOrchestrator,
        session_manager,
        mock_retrieve_chunks,
    ):
        # Session without report_ids should skip retrieval
        session = await session_manager.create_session(title="No reports")
        assistant_msg, citations = await orchestrator.process_message(
            session_id=session.id,
            user_message="Hello",
            retrieve_chunks=mock_retrieve_chunks,
        )
        assert assistant_msg is not None
        # Retrieve should not be called when no report_ids
        mock_retrieve_chunks.assert_not_called()

    # -- Mode mapping --

    def test_mode_to_strategy_single(self, orchestrator: ChatOrchestrator):
        assert orchestrator._mode_to_strategy("single") == "single_document"

    def test_mode_to_strategy_multi(self, orchestrator: ChatOrchestrator):
        assert orchestrator._mode_to_strategy("multi") == "multi_document"

    def test_mode_to_strategy_comparison(self, orchestrator: ChatOrchestrator):
        assert orchestrator._mode_to_strategy("comparison") == "comparison"

    def test_mode_to_strategy_unknown(self, orchestrator: ChatOrchestrator):
        # Unknown mode defaults to single_document
        assert orchestrator._mode_to_strategy("unknown") == "single_document"

    # -- Streaming --

    @pytest.mark.asyncio
    async def test_process_message_streaming_basic(
        self,
        session_manager,
        message_manager,
        citation_engine,
        mock_context_pipeline,
        mock_prompt_builder,
    ):
        """Test streaming path collects tokens and persists."""

        async def token_gen() -> AsyncIterator[StreamingChunk]:
            yield StreamingChunk(text="Hello")
            yield StreamingChunk(text=" world")
            yield StreamingChunk(text="", finish_reason="stop")

        provider = MagicMock()
        provider.generate_stream = MagicMock(return_value=token_gen())

        orch = ChatOrchestrator(
            session_manager=session_manager,
            message_manager=message_manager,
            citation_engine=citation_engine,
            context_pipeline=mock_context_pipeline,
            prompt_builder=mock_prompt_builder,
            llm_provider=provider,
        )

        session = await session_manager.create_session(report_ids=["r1"])
        chunks: list[StreamingChunk] = []
        async for chunk in orch.process_message_streaming(
            session_id=session.id,
            user_message="Hello",
        ):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0].text == "Hello"
        assert chunks[1].text == " world"
        assert chunks[2].finish_reason == "stop"

        # Verify assistant message was persisted
        msgs = await message_manager.list_messages(session.id)
        assistant_msgs = [m for m in msgs if m.role == "assistant"]
        assert len(assistant_msgs) >= 1
        assert assistant_msgs[-1].content == "Hello world"

    @pytest.mark.asyncio
    async def test_process_message_streaming_session_not_found(
        self,
        message_manager,
        citation_engine,
        mock_context_pipeline,
        mock_prompt_builder,
        mock_llm_provider,
    ):
        orch = ChatOrchestrator(
            session_manager=MagicMock(),
            message_manager=message_manager,
            citation_engine=citation_engine,
            context_pipeline=mock_context_pipeline,
            prompt_builder=mock_prompt_builder,
            llm_provider=mock_llm_provider,
        )
        # Make session_manager.get_session return None
        orch._session_mgr.get_session = AsyncMock(return_value=None)

        with pytest.raises(SessionNotFoundError):
            async for _ in orch.process_message_streaming(
                session_id="nonexistent", user_message="Hello"
            ):
                pass

    # -- Model conversion --

    def test_model_to_session(self, orchestrator: ChatOrchestrator):
        from src.ai_core.chat.database import ChatSessionModel

        model = ChatSessionModel(
            id="s1",
            title="Test",
            report_ids=["r1"],
            mode="single",
            archived=False,
        )
        session = orchestrator._model_to_session(model)
        assert session.id == "s1"
        assert session.title == "Test"
        assert session.report_ids == ["r1"]
        assert session.mode == "single"
        assert session.archived is False
