"""Tests for ChunkSelectionStrategy."""

from src.ai_core.context.chunk_selection import ChunkSelectionStrategy
from src.ai_core.context.models import ContextChunk


class TestChunkSelectionStrategy:
    def test_empty(self):
        selector = ChunkSelectionStrategy()
        assert selector.select([]) == []

    def test_sort_by_relevance(self):
        selector = ChunkSelectionStrategy()
        chunks = [
            ContextChunk(chunk_id="c1", content="a", score=0.3),
            ContextChunk(chunk_id="c2", content="b", score=0.9),
            ContextChunk(chunk_id="c3", content="c", score=0.6),
        ]
        result = selector.select(chunks)
        assert result[0].chunk_id == "c2"
        assert result[1].chunk_id == "c3"
        assert result[2].chunk_id == "c1"

    def test_deduplicate(self):
        selector = ChunkSelectionStrategy()
        chunks = [
            ContextChunk(chunk_id="c1", content="a", score=0.9),
            ContextChunk(chunk_id="c1", content="a", score=0.8),
            ContextChunk(chunk_id="c2", content="b", score=0.7),
        ]
        result = selector.select(chunks)
        assert len(result) == 2
        ids = [c.chunk_id for c in result]
        assert ids.count("c1") == 1

    def test_merge_adjacent_same_source(self):
        selector = ChunkSelectionStrategy()
        chunks = [
            ContextChunk(
                chunk_id="c1", content="part1", score=0.9, source_id="doc1", section_name="sec1"
            ),
            ContextChunk(
                chunk_id="c2", content="part2", score=0.8, source_id="doc1", section_name="sec1"
            ),
            ContextChunk(
                chunk_id="c3", content="other", score=0.7, source_id="doc2", section_name="sec2"
            ),
        ]
        result = selector.select(chunks)
        # First two should merge
        assert len(result) == 2
        assert "part1" in result[0].content

    def test_preserve_citations(self):
        selector = ChunkSelectionStrategy()
        chunks = [
            ContextChunk(chunk_id="c1", content="a", score=0.5, source_id="src1"),
        ]
        result = selector.select(chunks)
        assert "src1" in result[0].citations

    def test_max_chunks(self):
        selector = ChunkSelectionStrategy()
        chunks = [
            ContextChunk(chunk_id=f"c{i}", content=f"content{i}", score=1.0 - i * 0.05)
            for i in range(50)
        ]
        result = selector.select(chunks)
        assert len(result) <= 20  # default max_chunks

    def test_expand_parent_child(self):
        selector = ChunkSelectionStrategy()
        chunks = [
            ContextChunk(
                chunk_id="c1", content="child", score=0.9, metadata={"parent_chunk_id": "p1"}
            ),
        ]
        result = selector.select(chunks)
        assert any("parent:p1" in c.citations for c in result)
