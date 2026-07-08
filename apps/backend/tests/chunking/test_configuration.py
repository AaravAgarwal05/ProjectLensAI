"""Tests for chunking configuration."""
from src.ai_core.chunking.configuration import ChunkingConfiguration


class TestChunkingConfiguration:
    def test_defaults(self):
        cfg = ChunkingConfiguration()
        assert cfg.chunk_size == 1000
        assert cfg.chunk_overlap == 200
        assert cfg.min_chunk_size == 100
        assert cfg.max_chunk_size == 2000
        assert cfg.separator_priority == ["\n\n", "\n", ".", " ", ""]
        assert cfg.preserve_paragraphs is True
        assert cfg.max_chunks == 0

    def test_default_classmethod(self):
        cfg = ChunkingConfiguration.default()
        assert cfg.chunk_size == 1000

    def test_merge(self):
        cfg = ChunkingConfiguration(chunk_size=500, preserve_paragraphs=False)
        merged = cfg.merge({"chunk_size": 800})
        assert merged.chunk_size == 800
        assert merged.preserve_paragraphs is False  # unchanged
        assert merged.chunk_overlap == 200

    def test_merge_new_key(self):
        cfg = ChunkingConfiguration()
        merged = cfg.merge({"extra": {"strategy": "recursive"}})
        assert merged.extra["strategy"] == "recursive"