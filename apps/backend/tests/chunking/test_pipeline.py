"""Tests for ChunkingPipeline."""
from shared.models import DocumentMetadata, ParsedDocument

from src.ai_core.chunking.configuration import ChunkingConfiguration
from src.ai_core.chunking.exceptions import ChunkerNotFoundError
from src.ai_core.chunking.factory import ChunkingFactory
from src.ai_core.chunking.hooks import HookRegistry
from src.ai_core.chunking.pipeline import ChunkingPipeline
from src.ai_core.chunking.registry import ChunkingRegistry
from src.ai_core.chunking.strategies.fixed import FixedChunker
from src.ai_core.chunking.strategies.heading_aware import HeadingAwareChunker
from src.ai_core.chunking.strategies.recursive import RecursiveChunker
from src.ai_core.chunking.validation import ValidationEngine


def _make_doc(text: str = "Hello world. " * 20) -> ParsedDocument:
    return ParsedDocument(
        report_id="test",
        parser_used="test",
        metadata=DocumentMetadata(title="Test", author="Author", language="en"),
        clean_text=text,
    )


def _make_factory() -> ChunkingFactory:
    reg = ChunkingRegistry()
    reg.register("fixed", FixedChunker)
    reg.register("recursive", RecursiveChunker)
    reg.register("heading_aware", HeadingAwareChunker)
    return ChunkingFactory(reg)


class TestChunkingPipeline:
    def test_run_default_strategy(self):
        factory = _make_factory()
        pipeline = ChunkingPipeline(factory)
        doc = _make_doc()
        result = pipeline.run(doc)
        assert result.successful is True
        assert len(result.chunks) > 0
        # Default strategy is heading_aware
        assert result.statistics.source == "heading_aware"

    def test_run_fixed_strategy(self):
        factory = _make_factory()
        pipeline = ChunkingPipeline(factory)
        doc = _make_doc()
        result = pipeline.run(doc, strategy="fixed")
        assert result.successful is True
        assert result.statistics.source == "fixed"

    def test_run_recursive_strategy(self):
        factory = _make_factory()
        pipeline = ChunkingPipeline(factory)
        doc = _make_doc()
        result = pipeline.run(doc, strategy="recursive")
        assert result.successful is True
        assert result.statistics.source == "recursive"

    def test_run_with_validation(self):
        engine = ValidationEngine()
        factory = _make_factory()
        pipeline = ChunkingPipeline(factory, validation=engine)
        doc = _make_doc()
        result = pipeline.run(doc)
        assert result.successful is True

    def test_run_with_hooks(self):
        factory = _make_factory()
        hooks = HookRegistry()
        pipeline = ChunkingPipeline(factory, hooks=hooks)
        calls = []

        def hook(doc):
            calls.append("called")
            return doc

        hooks.register("before_chunking", hook)
        pipeline.run(_make_doc())
        assert len(calls) == 1

    def test_run_with_config(self):
        factory = _make_factory()
        pipeline = ChunkingPipeline(factory)
        doc = _make_doc("A" * 500)
        result = pipeline.run(doc, strategy="fixed", config=ChunkingConfiguration(chunk_size=100))
        assert result.successful is True

    def test_empty_document(self):
        factory = _make_factory()
        pipeline = ChunkingPipeline(factory)
        doc = _make_doc("")
        result = pipeline.run(doc)
        assert result.successful is False
        assert any("no clean_text" in e.lower() for e in result.errors)

    def test_unknown_strategy(self):
        factory = _make_factory()
        pipeline = ChunkingPipeline(factory)
        doc = _make_doc()
        result = pipeline.run(doc, strategy="nonexistent")
        assert result.successful is False

    def test_timing_populated(self):
        factory = _make_factory()
        pipeline = ChunkingPipeline(factory)
        doc = _make_doc()
        result = pipeline.run(doc)
        assert result.statistics.processing_time > 0

    def test_kwargs_forwarded(self):
        factory = _make_factory()
        pipeline = ChunkingPipeline(factory)
        doc = _make_doc()
        result = pipeline.run(doc, strategy="fixed", chunk_size=200)
        assert result.successful is True

    def test_hook_registry_property(self):
        hooks = HookRegistry()
        pipeline = ChunkingPipeline(hooks=hooks)
        assert pipeline.hooks is hooks

    def test_factory_property(self):
        factory = _make_factory()
        pipeline = ChunkingPipeline(factory=factory)
        assert pipeline.factory is factory