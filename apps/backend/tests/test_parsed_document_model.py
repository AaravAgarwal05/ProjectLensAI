"""Tests for the ParsedDocument Pydantic model and related types."""

from __future__ import annotations

from datetime import datetime

from shared.models.processing import (
    DocumentMetadata,
    Page,
    ParsedDocument,
    ProcessingStatistics,
    ProcessingWarning,
)


class TestParsedDocumentModel:
    """Suite for ParsedDocument model — serialization and defaults."""

    def test_parsed_document_serialization(self) -> None:
        """A ParsedDocument round-trips through model_dump / model_validate."""
        doc = ParsedDocument(
            parser_used="test_parser",
            raw_text="hello world",
            clean_text="hello world",
            metadata=DocumentMetadata(title="Test", word_count=2, char_count=11),
        )
        data = doc.model_dump()
        restored = ParsedDocument.model_validate(data)

        assert restored.parser_used == "test_parser"
        assert restored.raw_text == "hello world"
        assert restored.metadata.title == "Test"
        assert restored.metadata.word_count == 2

    def test_parsed_document_with_pages(self) -> None:
        """Pages are preserved with content and counts."""
        pages = [
            Page(number=1, content="Page one content", char_count=16, word_count=3),
            Page(number=2, content="Page two content", char_count=16, word_count=3),
        ]
        doc = ParsedDocument(
            parser_used="test",
            pages=pages,
            raw_text="Page one contentPage two content",
        )

        assert len(doc.pages) == 2
        assert doc.pages[0].number == 1
        assert doc.pages[0].content == "Page one content"
        assert doc.pages[1].number == 2
        assert doc.pages[1].word_count == 3

    def test_processing_statistics_timing(self) -> None:
        """Statistics stores timing fields correctly."""
        stats = ProcessingStatistics(
            parse_time_ms=150.5,
            clean_time_ms=42.3,
            metadata_time_ms=10.2,
            total_time_ms=203.0,
            page_count=10,
            raw_char_count=5000,
            clean_char_count=4800,
        )

        assert stats.parse_time_ms == 150.5
        assert stats.clean_time_ms == 42.3
        assert stats.metadata_time_ms == 10.2
        assert stats.total_time_ms == 203.0

    def test_page_content_counts(self) -> None:
        """Page char_count and word_count reflect actual content."""
        page = Page(
            number=1,
            content="Hello world! This is a test.",
            char_count=27,
            word_count=5,
        )

        assert page.char_count == 27
        assert page.word_count == 5

    def test_parsed_document_defaults(self) -> None:
        """ParsedDocument created with minimal args gets sensible defaults."""
        doc = ParsedDocument(parser_used="test")
        data = doc.model_dump()

        assert doc.raw_text == ""
        assert doc.clean_text == ""
        assert len(doc.pages) == 0
        assert len(doc.warnings) == 0
        assert doc.metadata.word_count == 0
        assert doc.metadata.char_count == 0
        assert doc.statistics.parse_time_ms == 0.0
        assert data["created_at"] is not None

    def test_parsed_document_with_warnings(self) -> None:
        """Warnings are stored and serialised correctly."""
        doc = ParsedDocument(
            parser_used="test",
            warnings=[
                ProcessingWarning(
                    stage="parse",
                    message="Empty document",
                    details={"file_path": "/tmp/test.pdf"},
                ),
            ],
        )
        data = doc.model_dump()

        assert len(doc.warnings) == 1
        assert doc.warnings[0].stage == "parse"
        assert doc.warnings[0].message == "Empty document"
        assert data["warnings"][0]["details"]["file_path"] == "/tmp/test.pdf"

    def test_created_at_auto_populated(self) -> None:
        """created_at is set automatically to the current UTC time."""
        before = datetime.utcnow()
        doc = ParsedDocument(parser_used="test")
        after = datetime.utcnow()

        assert before <= doc.created_at.replace(tzinfo=None) <= after
