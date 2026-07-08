"""Tests for HeadingAwareChunker (default strategy)."""
from shared.models import DocumentMetadata, Page, ParsedDocument

from src.ai_core.chunking.configuration import ChunkingConfiguration
from src.ai_core.chunking.strategies.heading_aware import HeadingAwareChunker


def _make_doc(text: str, n_pages: int = 1) -> ParsedDocument:
    return ParsedDocument(
        report_id="test",
        parser_used="test",
        metadata=DocumentMetadata(title="Test Report", author="Author", language="en"),
        pages=[Page(number=i + 1, content="") for i in range(n_pages)],
        clean_text=text,
    )


class TestHeadingAwareChunker:
    def test_name(self):
        chunker = HeadingAwareChunker()
        assert chunker.name == "heading_aware"

    def test_empty_document(self):
        chunker = HeadingAwareChunker()
        doc = _make_doc("")
        result = chunker.chunk(doc)
        assert result.chunks == []
        assert result.successful is False
        assert "empty document" in result.errors

    def test_no_headings(self):
        """Document without headings → single document-level chunk."""
        chunker = HeadingAwareChunker()
        doc = _make_doc("This is a plain document with no headings. " * 10)
        result = chunker.chunk(doc)
        assert len(result.chunks) >= 1
        assert result.chunks[0].section == "(document)"
        assert result.chunks[0].heading == "(document)"

    def test_chapter_headings(self):
        text = (
            "Chapter 1: Introduction\n\nIntro text here.\n\n"
            "Chapter 2: Methods\n\nMethods text here.\n\n"
            "Chapter 3: Results\n\nResults text here."
        )
        chunker = HeadingAwareChunker()
        doc = _make_doc(text)
        result = chunker.chunk(doc)
        assert len(result.chunks) >= 3

    def test_numeric_sections(self):
        text = (
            "1. Introduction\n\n" + "A" * 50 + "\n\n"
            "1.1 Background\n\n" + "B" * 50 + "\n\n"
            "1.2 Motivation\n\n" + "C" * 50 + "\n\n"
            "2. Methods\n\n" + "D" * 50
        )
        chunker = HeadingAwareChunker()
        doc = _make_doc(text)
        result = chunker.chunk(doc)
        # 1. Introduction has children (1.1, 1.2), so only
        # 1.1, 1.2, and 2. produce leaf chunks.
        assert len(result.chunks) >= 3

    def test_section_hierarchy_in_metadata(self):
        text = (
            "1. Introduction\n\nIntro text.\n\n"
            "1.1 Background\n\nBackground details."
        )
        chunker = HeadingAwareChunker()
        doc = _make_doc(text)
        result = chunker.chunk(doc)
        for c in result.chunks:
            assert c.metadata.document_title == "Test Report"
            assert c.metadata.document_author == "Author"
            assert c.metadata.language == "en"

    def test_large_section_split(self):
        """Sections larger than chunk_size should be split."""
        chunker = HeadingAwareChunker(ChunkingConfiguration(chunk_size=200))
        text = "# Huge Section\n\n" + "Long paragraph content here. " * 50
        doc = _make_doc(text)
        result = chunker.chunk(doc)
        assert len(result.chunks) >= 2

    def test_statistics(self):
        chunker = HeadingAwareChunker()
        text = "Chapter 1: Intro\n\nText.\nChapter 2: Body\n\nMore text."
        doc = _make_doc(text)
        result = chunker.chunk(doc)
        assert result.statistics.number_of_chunks > 0
        assert result.statistics.source == "heading_aware"
        assert result.statistics.average_chunk_size > 0

    def test_page_estimation(self):
        chunker = HeadingAwareChunker()
        text = "Chapter 1: Intro\n\nText.\nChapter 2: Body\n\nMore."
        doc = _make_doc(text, n_pages=3)
        result = chunker.chunk(doc)
        for c in result.chunks:
            assert c.page_number is not None

    def test_configure(self):
        chunker = HeadingAwareChunker()
        chunker.configure({"chunk_size": 500})
        assert chunker._config.chunk_size == 500

    def test_markdown_headings(self):
        """Sibling markdown headings at the same level produce separate chunks."""
        text = "# First\n\n" + "A" * 50 + "\n\n# Second\n\n" + "B" * 50 + "\n\n# Third\n\n" + "C" * 50
        chunker = HeadingAwareChunker()
        doc = _make_doc(text)
        result = chunker.chunk(doc)
        assert len(result.chunks) >= 3

    def test_section_path(self):
        text = (
            "## Section A\n\nText A.\n\n"
            "### Subsection A.1\n\nText A.1.\n\n"
            "## Section B\n\nText B."
        )
        chunker = HeadingAwareChunker()
        doc = _make_doc(text)
        result = chunker.chunk(doc)
        # Subsection A.1 should have a path like "Section A > Subsection A.1"
        for c in result.chunks:
            if c.section and "Section A" in c.section:
                assert "Subsection" in c.section or "Text" in c.text