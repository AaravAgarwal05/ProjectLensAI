"""Tests for chunking registry and factory."""
import pytest

from src.ai_core.chunking.exceptions import ChunkerNotFoundError
from src.ai_core.chunking.factory import ChunkingFactory
from src.ai_core.chunking.registry import ChunkingRegistry
from src.ai_core.chunking.strategies.fixed import FixedChunker
from src.ai_core.chunking.strategies.heading_aware import HeadingAwareChunker
from src.ai_core.chunking.strategies.recursive import RecursiveChunker


class TestChunkingRegistry:
    def test_register_and_get(self):
        reg = ChunkingRegistry()
        reg.register("test_chunker", FixedChunker)
        chunker = reg.get("test_chunker")
        assert isinstance(chunker, FixedChunker)
        assert chunker.name == "fixed"

    def test_get_unknown(self):
        reg = ChunkingRegistry()
        with pytest.raises(ChunkerNotFoundError):
            reg.get("nonexistent")

    def test_registered_strategies(self):
        reg = ChunkingRegistry()
        reg.register("fixed", FixedChunker)
        reg.register("recursive", RecursiveChunker)
        reg.register("heading_aware", HeadingAwareChunker)
        names = set(reg.list())
        assert "fixed" in names
        assert "recursive" in names
        assert "heading_aware" in names

    def test_lazy_instantiation(self):
        reg = ChunkingRegistry()
        reg.register("fixed", FixedChunker)
        c1 = reg.get("fixed")
        c2 = reg.get("fixed")
        assert c1 is c2  # cached

    def test_unregister(self):
        reg = ChunkingRegistry()
        reg.register("fixed", FixedChunker)
        reg.unregister("fixed")
        assert "fixed" not in reg.list()
        # unregister on missing is a no-op (no crash)
        reg.unregister("fixed")

    def test_double_register_default_false(self):
        reg = ChunkingRegistry()
        reg.register("fixed", FixedChunker)
        with pytest.raises(ValueError, match="already registered"):
            reg.register("fixed", FixedChunker)

    def test_double_register_overwrite(self):
        reg = ChunkingRegistry()
        reg.register("fixed", FixedChunker)

        class FakeChunker(FixedChunker):
            @property
            def name(self):
                return "fake"

        reg.register("fixed", FakeChunker, overwrite=True)
        chunker = reg.get("fixed")
        assert isinstance(chunker, FakeChunker)


class TestChunkingFactory:
    def test_create(self):
        factory = ChunkingFactory()
        factory.registry.register("fixed", FixedChunker)
        chunker = factory.create("fixed")
        assert isinstance(chunker, FixedChunker)

    def test_create_unknown(self):
        factory = ChunkingFactory()
        with pytest.raises(ChunkerNotFoundError):
            factory.create("unknown")

    def test_create_with_aliases(self):
        factory = ChunkingFactory()
        factory.registry.register("heading_aware", HeadingAwareChunker)
        factory.registry.register("recursive", RecursiveChunker)

        # "default" alias → heading_aware
        chunker = factory.create("default")
        assert isinstance(chunker, HeadingAwareChunker)

        # "heading-aware" alias → heading_aware
        chunker = factory.create("heading-aware")
        assert isinstance(chunker, HeadingAwareChunker)

    def test_create_case_insensitive(self):
        factory = ChunkingFactory()
        factory.registry.register("fixed", FixedChunker)
        chunker = factory.create("FIXED")
        assert isinstance(chunker, FixedChunker)