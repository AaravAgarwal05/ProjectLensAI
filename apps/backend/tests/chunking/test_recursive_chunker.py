"""Tests for RecursiveChunker."""
from shared.models import DocumentMetadata, ParsedDocument

from src.ai_core.chunking.configuration import ChunkingConfiguration
from src.ai_core.chunking.strategies.recursive import RecursiveChunker


def _make_doc(text: str) -> ParsedDocument:
    return ParsedDocument(
        report_id="test",
        parser_used="test",
        metadata=DocumentMetadata(title="Test", author="Author", language="en"),
        clean_text=text,
    )


class TestRecursiveChunker:
    def test_name(self):
        chunker = RecursiveChunker()
        assert chunker.name == "recursive"

    def test_empty_document(self):
        chunker = RecursiveChunker()
        doc = _make_doc("")
        result = chunker.chunk(doc)
        assert result.chunks == []
        assert result.successful is False

    def test_single_chunk_small_text(self):
        chunker = RecursiveChunker()
        doc = _make_doc("Small text.")
        result = chunker.chunk(doc)
        assert len(result.chunks) == 1

    def test_paragraph_splitting(self):
        chunker = RecursiveChunker(ChunkingConfiguration(chunk_size=50, min_chunk_size=10))
        text = "\n\n".join([f"This is paragraph number {i}. It has multiple sentences." for i in range(20)])
        doc = _make_doc(text)
        result = chunker.chunk(doc)
        assert len(result.chunks) > 1
        for c in result.chunks:
            assert len(c.text) > 0

    def test_heading_splitting(self):
        chunker = RecursiveChunker(ChunkingConfiguration(chunk_size=80, min_chunk_size=10))
        text = (
            "# Introduction\n\n"
            + "Intro text here. " * 10 + "\n\n"
            "# Chapter 1\n\n"
            + "First chapter content. " * 10 + "\n\n"
            "# Chapter 2\n\n"
            + "Second chapter content. " * 10
        )
        doc = _make_doc(text)
        result = chunker.chunk(doc)
        assert len(result.chunks) >= 3

    def test_statistics(self):
        chunker = RecursiveChunker()
        doc = _make_doc("Sentence one. " * 100)
        result = chunker.chunk(doc)
        assert result.statistics.number_of_chunks > 0
        assert result.statistics.source == "recursive"

    def test_tiny_chunk_merging(self):
        chunker = RecursiveChunker(ChunkingConfiguration(chunk_size=1000))
        text = "A" * 50 + "\n\n" + "B" * 50
        doc = _make_doc(text)
        result = chunker.chunk(doc)
        assert len(result.chunks) >= 1

    def test_configure(self):
        chunker = RecursiveChunker()
        chunker.configure({"chunk_size": 300})
        assert chunker._config.chunk_size == 300

    def test_split_by_heading(self):
        chunker = RecursiveChunker()
        text = "## Intro\n\nSome intro.\n## Details\n\nMore details."
        segments = chunker._split_by_heading(text)
        assert len(segments) >= 2