"""Shared test fixtures for chat tests.

Import helpers directly since tests run with --noconftest.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.ai_core.chat.citations import CitationEngine
from src.ai_core.chat.database import ChatMessageModel, ChatSessionModel
from src.ai_core.chat.message_manager import MessageManager
from src.ai_core.chat.models import (
    ChatMessage,
    ChatSession,
    CitationReference,
    MessageRole,
)
from src.ai_core.chat.orchestrator import ChatOrchestrator
from src.ai_core.chat.session_manager import SessionManager
from src.ai_core.chat.validation import ChatValidationEngine
from src.ai_core.context.models import ContextChunk


@pytest.fixture
async def async_db():
    """Create an in-memory SQLite database for testing.

    Only creates chat tables to avoid conflicts with
    PostgreSQL-specific types in other models.
    """
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        # Create only chat tables
        await conn.run_sync(ChatSessionModel.__table__.create)
        await conn.run_sync(ChatMessageModel.__table__.create)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def session_manager(async_db: AsyncSession) -> SessionManager:
    return SessionManager(async_db)


@pytest.fixture
def message_manager(async_db: AsyncSession) -> MessageManager:
    return MessageManager(async_db)


@pytest.fixture
def citation_engine() -> CitationEngine:
    return CitationEngine()


@pytest.fixture
def validation_engine() -> ChatValidationEngine:
    return ChatValidationEngine(max_message_length=10000)


@pytest.fixture
def sample_context_chunks() -> list[ContextChunk]:
    return [
        ContextChunk(
            chunk_id="chunk1",
            content="The ML model uses a random forest algorithm.",
            score=0.95,
            source_id="report_1",
            source_title="Technical Report",
            page_number=5,
            section_name="Methodology",
        ),
        ContextChunk(
            chunk_id="chunk2",
            content="Results show 94% accuracy on the test set.",
            score=0.88,
            source_id="report_1",
            source_title="Technical Report",
            page_number=10,
            section_name="Results",
        ),
        ContextChunk(
            chunk_id="chunk3",
            content="The dataset contains 50,000 labeled samples.",
            score=0.72,
            source_id="report_2",
            source_title="Dataset Overview",
            page_number=2,
            section_name="Data Collection",
        ),
    ]


@pytest.fixture
def sample_chat_session() -> ChatSession:
    now = datetime.now(UTC)
    return ChatSession(
        id="session-1",
        title="Test Chat",
        report_ids=["report_1"],
        mode="single",
        created_at=now,
        updated_at=now,
        archived=False,
    )


@pytest.fixture
def sample_chat_message() -> ChatMessage:
    now = datetime.now(UTC)
    return ChatMessage(
        id="msg-1",
        session_id="session-1",
        role=MessageRole.USER.value,
        content="What algorithm was used?",
        created_at=now,
    )


def make_mock_orchestrator(
    response_text: str = "The random forest algorithm was used.",
    citations: list[CitationReference] | None = None,
) -> ChatOrchestrator:
    """Create a mock orchestrator for testing."""
    mock = MagicMock(spec=ChatOrchestrator)

    if citations is None:
        citations = [
            CitationReference(
                report_id="report_1",
                report_title="Technical Report",
                page_number=5,
                section_name="Methodology",
                chunk_id="chunk1",
                score=0.95,
            )
        ]

    async def mock_process(
        *args: Any, **kwargs: Any
    ) -> tuple[ChatMessage, list[CitationReference]]:
        now = datetime.now(UTC)
        return (
            ChatMessage(
                id="assistant-1",
                session_id=kwargs.get("session_id", "session-1"),
                role=MessageRole.ASSISTANT.value,
                content=response_text,
                citations=citations,
                created_at=now,
            ),
            citations,
        )

    mock.process_message = mock_process
    return mock
