"""Tests for MetadataExtractor — extracting DocumentMetadata from file path and content."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.document_processing.metadata import MetadataExtractor


class TestMetadataExtractor:
    """Suite for MetadataExtractor."""

    def test_extracts_basic_metadata(self, tmp_path: pytest.TempPathFactory) -> None:
        """Standard file yields title derived from the filename, with word/char counts."""
        file_path = tmp_path / "annual_report_2024.pdf"
        file_path.write_text("This is a test document with several words in it.")
        content = "This is a test document with several words in it."

        meta = MetadataExtractor.extract(file_path=str(file_path), content=content)

        assert meta.title is not None
        assert "annual report 2024" in meta.title.lower()
        assert meta.word_count == 10
        assert meta.char_count == len(content)
        assert meta.processed_by == "pipeline-v1"

    def test_handles_missing_metadata_gracefully(self) -> None:
        """Non-existent file path returns sensible defaults instead of raising."""
        meta = MetadataExtractor.extract(
            file_path="/nonexistent/path/unknown.docx",
            content="",
        )

        assert meta.title == "unknown"
        assert meta.author is None
        assert meta.subject is None
        assert meta.keywords == []
        assert meta.word_count == 0
        assert meta.char_count == 0
        assert meta.language is None

    def test_accepts_parser_metadata_overrides(self) -> None:
        """Parser-provided metadata (title, author, etc.) takes precedence."""
        parser_meta = {
            "title": "Override Title",
            "author": "Jane Doe",
            "subject": "Override Subject",
            "page_count": 42,
        }
        meta = MetadataExtractor.extract(
            file_path="/some/path/document.pdf",
            content="Some random content",
            parser_metadata=parser_meta,
        )

        assert meta.title == "Override Title"
        assert meta.author == "Jane Doe"
        assert meta.subject == "Override Subject"
        assert meta.page_count == 42

    def test_counts_words_and_chars_correctly(self) -> None:
        """Word and character counts match the provided content string."""
        content = "  Hello   world!  This\tis\na\ntest.  "
        meta = MetadataExtractor.extract(
            file_path="/tmp/test.txt",
            content=content,
        )

        # .split() handles all whitespace, so word count = 6
        assert meta.word_count == 6
        assert meta.char_count == len(content)

    def test_parser_metadata_extra_fields_preserved(self) -> None:
        """Unconsumed parser metadata keys end up in the extra dict."""
        parser_meta = {
            "title": "Title",
            "custom_field": "custom_value",
            "another_one": 42,
        }
        meta = MetadataExtractor.extract(
            file_path="/tmp/test.pdf",
            content="something",
            parser_metadata=parser_meta,
        )

        # 'title' is consumed, 'custom_field' and 'another_one' should be in extra
        assert meta.extra.get("custom_field") == "custom_value"
        assert meta.extra.get("another_one") == 42
        # Consumed keys are not in extra
        assert "title" not in meta.extra
        assert "author" not in meta.extra

    def test_creation_date_from_stat(self, tmp_path: pytest.TempPathFactory) -> None:
        """When no parser_metadata is given, creation_date falls back to file ctime."""
        file_path = tmp_path / "report.txt"
        file_path.write_text("content")

        meta = MetadataExtractor.extract(file_path=str(file_path), content="content")

        # Should be a datetime from the file's ctime
        assert meta.creation_date is not None
        assert isinstance(meta.creation_date, datetime)

    def test_creation_date_from_parser_metadata(self) -> None:
        """Parser-supplied creation_date is used when provided."""
        dt = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        meta = MetadataExtractor.extract(
            file_path="/tmp/test.pdf",
            content="content",
            parser_metadata={"creation_date": dt},
        )

        assert meta.creation_date == dt
