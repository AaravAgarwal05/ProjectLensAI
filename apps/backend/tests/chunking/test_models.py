"""Tests for chunking models."""
import pytest
from pydantic import ValidationError

from src.ai_core.chunking.models import Chunk, ChunkMetadata, ChunkStatistics, ChunkingResult


class TestChunkMetadata:
    def test_defaults(self):
        meta = ChunkMetadata()
        assert meta.page_number is None
        assert meta.section is None
        assert meta.heading is None
        assert meta.source == "unknown"
        assert meta.extra == {}

    def test_all_fields(self):
        meta = ChunkMetadata(
            page_number=1,
            section="Chapter 1",
            heading="Introduction",
            source="test",
            document_title="Test Report",
            document_author="Author",
            language="en",
            extra={"key": "val"},
        )
        assert meta.page_number == 1
        assert meta.section == "Chapter 1"
        assert meta.heading == "Introduction"
        assert meta.document_title == "Test Report"
        assert meta.extra["key"] == "val"


class TestChunk:
    def test_defaults(self):
        chunk = Chunk(text="hello world")
        assert chunk.chunk_id is not None
        assert chunk.text == "hello world"
        assert chunk.chunk_index == 0
        assert chunk.token_count == 0
        assert chunk.metadata.source == "unknown"
        assert chunk.created_at is not None

    def test_frozen(self):
        chunk = Chunk(text="test")
        with pytest.raises(ValidationError):
            chunk.text = "changed"

    def test_all_fields(self):
        meta = ChunkMetadata(page_number=1, source="fixed")
        chunk = Chunk(
            chunk_index=0,
            report_id="r1",
            report_version_id="v1",
            page_number=1,
            start_offset=0,
            end_offset=10,
            text="hello world",
            token_count=3,
            section="Intro",
            heading="Intro",
            metadata=meta,
        )
        assert chunk.report_id == "r1"
        assert chunk.text == "hello world"
        assert chunk.token_count == 3
        assert chunk.metadata.page_number == 1

    def test_text_required(self):
        with pytest.raises(ValidationError):
            Chunk()

    def test_chunk_id_unique(self):
        c1 = Chunk(text="a")
        c2 = Chunk(text="b")
        assert c1.chunk_id != c2.chunk_id


class TestChunkStatistics:
    def test_defaults(self):
        stats = ChunkStatistics()
        assert stats.number_of_chunks == 0
        assert stats.average_chunk_size == 0
        assert stats.processing_time == 0.0

    def test_round_trip(self):
        stats = ChunkStatistics(
            number_of_chunks=5,
            average_chunk_size=200.0,
            average_tokens_per_chunk=50.0,
            largest_chunk=300,
            smallest_chunk=100,
            processing_time=0.5,
            memory_usage=1024,
            source="heading_aware",
            chunk_size_std_dev=10.0,
        )
        assert stats.number_of_chunks == 5
        assert stats.average_chunk_size == 200.0
        assert stats.largest_chunk == 300
        assert stats.source == "heading_aware"


class TestChunkingResult:
    def test_defaults(self):
        result = ChunkingResult()
        assert result.chunks == []
        assert result.statistics.number_of_chunks == 0
        assert result.warnings == []
        assert result.errors == []
        assert result.successful is True

    def test_with_chunks(self):
        chunks = [Chunk(text="hello"), Chunk(text="world", chunk_index=1)]
        result = ChunkingResult(chunks=chunks)
        assert len(result.chunks) == 2
        assert result.chunks[0].text == "hello"
        assert result.chunks[1].text == "world"

    def test_not_successful(self):
        result = ChunkingResult(
            chunks=[],
            errors=["empty document"],
            successful=False,
        )
        assert result.successful is False
        assert "empty document" in result.errors