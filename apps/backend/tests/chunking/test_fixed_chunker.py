"""Tests for FixedChunker."""
from shared.models.processing import DocumentMetadata, Page, ParsedDocument

from src.ai_core.chunking.configuration import ChunkingConfiguration
from src.ai_core.chunking.strategies.fixed import FixedChunker


def _make_doc(text: str, n_pages: int = 1) -> ParsedDocument:
    return ParsedDocument(
        report_id="test_report",
        parser_used="test",
        metadata=DocumentMetadata(title="Test Report", author="Author", language="en"),
        pages=[Page(number=i + 1, content=text[i * 100 : (i + 1) * 100]) for i in range(n_pages)],
        clean_text=text,
    )


class TestFixedChunker:
    def test_name(self):
        chunker = FixedChunker()
        assert chunker.name == "fixed"

    def test_empty_document(self):
        chunker = FixedChunker()
        doc = _make_doc("")
        result = chunker.chunk(doc)
        assert result.chunks == []
        assert result.successful is False
        assert "empty document" in result.errors

    def test_single_chunk(self):
        chunker = FixedChunker(ChunkingConfiguration(chunk_size=1000))
        doc = _make_doc("Hello world. " * 10)
        result = chunker.chunk(doc)
        assert len(result.chunks) >= 1
        for c in result.chunks:
            assert c.text is not None
            assert c.token_count > 0
            assert c.metadata.source == "fixed"

    def test_multiple_chunks(self):
        chunker = FixedChunker(ChunkingConfiguration(chunk_size=100, chunk_overlap=0))
        text = "Word " * 200
        doc = _make_doc(text)
        result = chunker.chunk(doc)
        assert len(result.chunks) >= 10

    def test_overlap(self):
        chunker = FixedChunker(ChunkingConfiguration(chunk_size=100, chunk_overlap=30))
        doc = _make_doc("Paragraph " * 100)
        result = chunker.chunk(doc)
        assert len(result.chunks) > 1
        # Overlapping chunks share some text
        if len(result.chunks) > 1:
            assert result.chunks[0].end_offset > result.chunks[1].start_offset

    def test_statistics(self):
        chunker = FixedChunker(ChunkingConfiguration(chunk_size=200))
        doc = _make_doc("Content " * 50)
        result = chunker.chunk(doc)
        assert result.statistics.number_of_chunks > 0
        assert result.statistics.average_chunk_size > 0
        assert result.statistics.average_tokens_per_chunk > 0
        assert result.statistics.largest_chunk >= result.statistics.smallest_chunk
        assert result.statistics.source == "fixed"

    def test_page_estimation(self):
        chunker = FixedChunker()
        text = ("A" * 250 + "\n") * 6  # ~1500 chars across multiple pages
        doc = _make_doc(text, n_pages=5)
        result = chunker.chunk(doc)
        for chunk in result.chunks:
            assert chunk.page_number is not None

    def test_validate_empty(self):
        chunker = FixedChunker()
        doc = _make_doc("")
        warnings = chunker.validate(doc)
        assert len(warnings) > 0

    def test_configure(self):
        chunker = FixedChunker()
        chunker.configure({"chunk_size": 500})
        assert chunker._config.chunk_size == 500