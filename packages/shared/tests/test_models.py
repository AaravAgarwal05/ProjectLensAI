"""Tests for the shared domain model classes."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from shared.models.analysis import AnalysisResult, Citation
from shared.models.chat import Conversation, Message, Thread
from shared.models.common import APIResponse, ErrorResponse, PaginatedResponse
from shared.models.document import Document, DocumentChunk, DocumentMetadata
from shared.models.user import User, UserPreferences


# ---------------------------------------------------------------------------
# Document model tests
# ---------------------------------------------------------------------------


class TestDocumentMetadata:
    def test_default_values(self) -> None:
        meta = DocumentMetadata()
        assert meta.title is None
        assert meta.author is None
        assert meta.page_count is None
        assert meta.language == "en"
        assert meta.custom == {}

    def test_custom_values(self) -> None:
        meta = DocumentMetadata(
            title="Report",
            author="Alice",
            page_count=42,
            language="fr",
            custom={"project": "X"},
        )
        assert meta.title == "Report"
        assert meta.custom["project"] == "X"


class TestDocument:
    def test_frozen_instance(self) -> None:
        now = datetime.now(timezone.utc)
        doc = Document(
            filename="test.pdf",
            content_type="application/pdf",
            size=1024,
            created_at=now,
            updated_at=now,
        )
        assert isinstance(doc.id, UUID)
        assert doc.status == "pending"
        with pytest.raises(ValidationError):
            doc.filename = "changed.pdf"  # type: ignore[misc]

    def test_minimal_construction(self) -> None:
        now = datetime.now(timezone.utc)
        doc = Document(
            filename="doc.txt",
            content_type="text/plain",
            size=512,
            created_at=now,
            updated_at=now,
        )
        assert doc.filename == "doc.txt"
        assert isinstance(doc.metadata, DocumentMetadata)

    def test_serialisation_roundtrip(self) -> None:
        now = datetime.now(timezone.utc)
        doc = Document(
            filename="test.pdf",
            content_type="application/pdf",
            size=1024,
            created_at=now,
            updated_at=now,
        )
        data = doc.model_dump()
        restored = Document.model_validate(data)
        assert restored.id == doc.id
        assert restored.filename == doc.filename


class TestDocumentChunk:
    def test_frozen_instance(self) -> None:
        chunk = DocumentChunk(
            document_id=UUID("00000000-0000-0000-0000-000000000001"),
            index=0,
            content="Hello world",
        )
        assert isinstance(chunk.id, UUID)
        assert chunk.embedding is None
        with pytest.raises(ValidationError):
            chunk.content = "mutated"  # type: ignore[misc]

    def test_with_embedding(self) -> None:
        chunk = DocumentChunk(
            document_id=UUID("00000000-0000-0000-0000-000000000001"),
            index=0,
            content="Hello",
            embedding=[0.1, 0.2, 0.3],
        )
        assert chunk.embedding == [0.1, 0.2, 0.3]


# ---------------------------------------------------------------------------
# Message / Conversation model tests
# ---------------------------------------------------------------------------


class TestMessage:
    def test_frozen_instance(self) -> None:
        msg = Message(
            conversation_id=UUID("00000000-0000-0000-0000-000000000001"),
            role="user",
            content="Hello!",
            created_at=datetime.now(timezone.utc),
        )
        assert isinstance(msg.id, UUID)
        with pytest.raises(ValidationError):
            msg.content = "changed"  # type: ignore[misc]


class TestConversation:
    def test_frozen_instance(self) -> None:
        now = datetime.now(timezone.utc)
        conv = Conversation(
            title="Test Chat",
            created_at=now,
            updated_at=now,
        )
        assert isinstance(conv.id, UUID)
        assert conv.messages == []

    def test_with_messages(self) -> None:
        now = datetime.now(timezone.utc)
        msg = Message(
            conversation_id=UUID("00000000-0000-0000-0000-000000000001"),
            role="user",
            content="Hi",
            created_at=now,
        )
        conv = Conversation(
            title="Chat",
            messages=[msg],
            created_at=now,
            updated_at=now,
        )
        assert len(conv.messages) == 1

    def test_serialisation_roundtrip(self) -> None:
        now = datetime.now(timezone.utc)
        conv = Conversation(
            title="Roundtrip",
            created_at=now,
            updated_at=now,
        )
        data = conv.model_dump()
        restored = Conversation.model_validate(data)
        assert restored.id == conv.id
        assert restored.title == "Roundtrip"


class TestThread:
    def test_minimal_construction(self) -> None:
        thread = Thread(
            parent_message_id=UUID("00000000-0000-0000-0000-000000000001"),
            created_at=datetime.now(timezone.utc),
        )
        assert isinstance(thread.id, UUID)
        assert thread.messages == []


# ---------------------------------------------------------------------------
# AnalysisResult model tests
# ---------------------------------------------------------------------------


class TestAnalysisResult:
    def test_frozen_instance(self) -> None:
        result = AnalysisResult(
            document_id=UUID("00000000-0000-0000-0000-000000000001"),
            analysis_type="summary",
            content="Analysis text",
            created_at=datetime.now(timezone.utc),
        )
        assert isinstance(result.id, UUID)
        assert result.citations == []
        assert result.confidence == 0.0

    def test_with_citations(self) -> None:
        citation = Citation(
            source="doc.pdf",
            page=5,
            text="Relevant excerpt",
            relevance_score=0.95,
        )
        result = AnalysisResult(
            document_id=UUID("00000000-0000-0000-0000-000000000001"),
            analysis_type="qa",
            content="Answer",
            citations=[citation],
            confidence=0.9,
            created_at=datetime.now(timezone.utc),
        )
        assert len(result.citations) == 1
        assert result.citations[0].source == "doc.pdf"

    def test_serialisation_roundtrip(self) -> None:
        now = datetime.now(timezone.utc)
        result = AnalysisResult(
            document_id=UUID("00000000-0000-0000-0000-000000000001"),
            analysis_type="summary",
            content="Summary text",
            created_at=now,
        )
        data = result.model_dump()
        restored = AnalysisResult.model_validate(data)
        assert restored.id == result.id


# ---------------------------------------------------------------------------
# Common model tests
# ---------------------------------------------------------------------------


class TestPaginatedResponse:
    def test_empty_page(self) -> None:
        page = PaginatedResponse[int](
            items=[],
            total=0,
            page=1,
            page_size=20,
            has_more=False,
        )
        assert page.items == []
        assert page.has_more is False

    def test_with_items(self) -> None:
        page = PaginatedResponse[str](
            items=["a", "b"],
            total=2,
            page=1,
            page_size=20,
            has_more=False,
        )
        assert len(page.items) == 2

    def test_has_more(self) -> None:
        page = PaginatedResponse[str](
            items=["a", "b", "c"],
            total=25,
            page=1,
            page_size=3,
            has_more=True,
        )
        assert page.has_more is True


class TestAPIResponse:
    def test_success(self) -> None:
        resp = APIResponse[str](success=True, data="ok")
        assert resp.success is True
        assert resp.data == "ok"
        assert resp.error is None

    def test_error(self) -> None:
        resp = APIResponse[str](
            success=False,
            error="Something went wrong",
        )
        assert resp.success is False
        assert resp.error == "Something went wrong"

    def test_timestamp_defaults(self) -> None:
        resp = APIResponse[str](success=True, data="data")
        assert resp.timestamp is not None


class TestErrorResponse:
    def test_minimal(self) -> None:
        err = ErrorResponse(code="NOT_FOUND", message="Resource not found")
        assert err.code == "NOT_FOUND"
        assert err.details is None

    def test_with_details(self) -> None:
        err = ErrorResponse(
            code="VALIDATION_ERROR",
            message="Invalid input",
            details={"field": "email", "reason": "bad format"},
        )
        assert err.details is not None
        assert err.details["field"] == "email"


# ---------------------------------------------------------------------------
# User model tests
# ---------------------------------------------------------------------------


class TestUser:
    def test_frozen_instance(self) -> None:
        now = datetime.now(timezone.utc)
        user = User(
            email="alice@example.com",
            username="alice",
            created_at=now,
            updated_at=now,
        )
        assert isinstance(user.id, UUID)
        assert user.role == "user"
        assert user.is_active is True
        with pytest.raises(ValidationError):
            user.email = "changed@example.com"  # type: ignore[misc]


class TestUserPreferences:
    def test_default_values(self) -> None:
        prefs = UserPreferences()
        assert prefs.theme == "light"
        assert prefs.language == "en"
        assert prefs.notifications_enabled is True
