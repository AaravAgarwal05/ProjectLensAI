"""Tests for ProcessingPipeline — orchestrator for parse -> clean -> metadata extraction."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from shared.models.processing import (
    DocumentMetadata,
    Page,
    ParsedDocument,
    ProcessingStatistics,
)
from src.document_processing.cleaners.base import CleaningPipeline, TextCleaner
from src.document_processing.exceptions import ProcessingError as ProcessingErrorException
from src.document_processing.metadata import MetadataExtractor
from src.document_processing.parsers.base import BaseParser
from src.document_processing.parsers.registry import ParserRegistry
from src.document_processing.pipeline import ProcessingPipeline, ProcessingContext


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_parser() -> BaseParser:
    """A mock parser that returns a simple ParsedDocument."""
    parser = MagicMock(spec=BaseParser)
    parser.name = "mock_parser"

    async def _parse(file_path: str) -> ParsedDocument:
        return ParsedDocument(
            parser_used="mock_parser",
            raw_text="raw content here",
            clean_text="",
            metadata=DocumentMetadata(title="Doc Title"),
            pages=[Page(number=1, content="raw content here", char_count=17, word_count=3)],
        )

    parser.parse = AsyncMock(side_effect=_parse)
    return parser


@pytest.fixture
def mock_cleaner() -> TextCleaner:
    """A mock cleaner that uppercases text."""
    cleaner = MagicMock(spec=TextCleaner)
    cleaner.name = "mock_cleaner"
    cleaner.clean.side_effect = lambda text: text.upper()
    return cleaner


@pytest.fixture
def parser_registry(mock_parser: BaseParser) -> ParserRegistry:
    """A ParserRegistry pre-registered with the mock parser."""
    registry = ParserRegistry()

    class _RegisteredParser(BaseParser):
        @property
        def name(self) -> str:
            return mock_parser.name

        @classmethod
        def supported_formats(cls) -> list[str]:
            return ["mock"]

        async def parse(self, file_path: str) -> ParsedDocument:
            return await mock_parser.parse(file_path)

    registry.register(_RegisteredParser)
    return registry


@pytest.fixture
def cleaning_pipeline(mock_cleaner: TextCleaner) -> CleaningPipeline:
    """A CleaningPipeline with the mock cleaner."""
    return CleaningPipeline([mock_cleaner])


@pytest.fixture
def pipeline(
    parser_registry: ParserRegistry,
    cleaning_pipeline: CleaningPipeline,
) -> ProcessingPipeline:
    """A ProcessingPipeline with mocked sub-components."""
    return ProcessingPipeline(
        parser_registry=parser_registry,
        cleaner_pipeline=cleaning_pipeline,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestProcessingPipeline:
    """Suite for ProcessingPipeline orchestration."""

    @pytest.mark.asyncio
    async def test_pipeline_orchestrates_parse_clean_metadata(
        self,
        pipeline: ProcessingPipeline,
        mock_parser: BaseParser,
        mock_cleaner: TextCleaner,
    ) -> None:
        """Pipeline runs parse -> clean -> metadata and returns a parsed doc."""
        result = await pipeline.run("/fake/file.mock")

        # Parse stage
        mock_parser.parse.assert_awaited_once_with("/fake/file.mock")

        # Clean stage — the raw text 'raw content here' should be uppercased
        assert result.raw_text == "raw content here"
        assert result.clean_text == "RAW CONTENT HERE"

        # Metadata is populated
        assert result.metadata is not None
        assert result.metadata.word_count > 0
        assert result.metadata.char_count > 0

        # Statistics are populated
        assert result.statistics is not None
        assert result.statistics.parse_time_ms >= 0
        assert result.statistics.clean_time_ms >= 0
        assert result.statistics.metadata_time_ms >= 0

    @pytest.mark.asyncio
    async def test_pipeline_hooks_fire_in_order(
        self,
        parser_registry: ParserRegistry,
        cleaning_pipeline: CleaningPipeline,
    ) -> None:
        """Lifecycle hooks are invoked in the correct sequence."""
        calls: list[str] = []

        class TrackingHook:
            def on_before_parse(self, ctx: ProcessingContext) -> None:
                calls.append("before_parse")

            def on_after_parse(self, ctx: ProcessingContext) -> None:
                calls.append("after_parse")

            def on_before_clean(self, ctx: ProcessingContext) -> None:
                calls.append("before_clean")

            def on_after_clean(self, ctx: ProcessingContext) -> None:
                calls.append("after_clean")

            def on_before_metadata(self, ctx: ProcessingContext) -> None:
                calls.append("before_metadata")

            def on_after_metadata(self, ctx: ProcessingContext) -> None:
                calls.append("after_metadata")

            def on_complete(self, ctx: ProcessingContext) -> None:
                calls.append("complete")

        pipeline = ProcessingPipeline(
            parser_registry=parser_registry,
            cleaner_pipeline=cleaning_pipeline,
            hooks=[TrackingHook()],
        )

        await pipeline.run("/fake/file.mock")

        assert calls == [
            "before_parse",
            "after_parse",
            "before_clean",
            "after_clean",
            "before_metadata",
            "after_metadata",
            "complete",
        ]

    @pytest.mark.asyncio
    async def test_pipeline_calls_on_error_on_failure(
        self,
    ) -> None:
        """When processing fails, on_error hooks fire and the exception is re-raised."""
        error_call_ctx: ProcessingContext | None = None
        error_call_exc: Exception | None = None

        class ErrorHook:
            def on_error(self, ctx: ProcessingContext, error: Exception) -> None:
                nonlocal error_call_ctx, error_call_exc
                error_call_ctx = ctx
                error_call_exc = error

        # A registry with no parsers registered — get() will raise ParserNotFoundError.
        registry = ParserRegistry()
        pipeline = ProcessingPipeline(
            parser_registry=registry,
            cleaner_pipeline=None,
            hooks=[ErrorHook()],
        )

        with pytest.raises(ProcessingErrorException):
            await pipeline.run("/fake/file.unknown")

        assert error_call_ctx is not None
        assert error_call_exc is not None
        assert error_call_ctx.status == "error"

    @pytest.mark.asyncio
    async def test_pipeline_passes_context_through_all_stages(
        self,
        pipeline: ProcessingPipeline,
    ) -> None:
        """The ProcessingContext tracks file_path, status, and stage transitions."""
        contexts: list[ProcessingContext] = []

        class ContextCaptureHook:
            def on_before_parse(self, ctx: ProcessingContext) -> None:
                contexts.append(ctx)

        pipeline.register_hook(ContextCaptureHook())

        result = await pipeline.run("/fake/file.mock")

        ctx = contexts[0]
        assert ctx.file_path == "/fake/file.mock"
        # After run, the context has the parsed doc
        assert ctx.parsed_doc is not None
        assert ctx.parsed_doc.parser_used == "mock_parser"

    @pytest.mark.asyncio
    async def test_pipeline_statistics_populated(
        self,
        pipeline: ProcessingPipeline,
    ) -> None:
        """ProcessingStatistics is fully populated after a successful run."""
        result = await pipeline.run("/fake/file.mock")

        stats = result.statistics
        assert stats.parse_time_ms >= 0
        assert stats.clean_time_ms >= 0
        assert stats.metadata_time_ms >= 0
        assert stats.total_time_ms > 0
        assert stats.page_count == 1
        assert stats.raw_char_count == len("raw content here")
        assert stats.clean_char_count == len("RAW CONTENT HERE")

    @pytest.mark.asyncio
    async def test_pipeline_skips_cleaner_when_none(
        self,
        parser_registry: ParserRegistry,
    ) -> None:
        """When cleaner_pipeline is None, clean_text is set from raw_text."""
        pipeline = ProcessingPipeline(parser_registry=parser_registry, cleaner_pipeline=None)

        result = await pipeline.run("/fake/file.mock")

        assert result.clean_text == result.raw_text
        assert result.statistics.clean_time_ms == 0.0

    @pytest.mark.asyncio
    async def test_pipeline_propagates_parser_exception(self) -> None:
        """If the parser raises, the pipeline re-raises as ProcessingErrorException."""
        registry = ParserRegistry()

        class BrokenParser(BaseParser):
            @property
            def name(self) -> str:
                return "broken"

            @classmethod
            def supported_formats(cls) -> list[str]:
                return ["brk"]

            async def parse(self, file_path: str) -> ParsedDocument:
                raise RuntimeError("parser exploded")

        registry.register(BrokenParser)
        pipeline = ProcessingPipeline(parser_registry=registry, cleaner_pipeline=None)

        with pytest.raises(ProcessingErrorException) as exc_info:
            await pipeline.run("/fake/file.brk")

        assert "parser exploded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_hook_exception_does_not_crash_pipeline(
        self,
        parser_registry: ParserRegistry,
        cleaning_pipeline: CleaningPipeline,
    ) -> None:
        """If a hook raises, the pipeline logs and continues (hook failure is
        never propagated)."""

        class ExplodingHook:
            def on_after_parse(self, ctx: ProcessingContext) -> None:
                raise ValueError("hook error")

        pipeline = ProcessingPipeline(
            parser_registry=parser_registry,
            cleaner_pipeline=cleaning_pipeline,
            hooks=[ExplodingHook()],
        )

        # Should not raise — the hook error is suppressed.
        result = await pipeline.run("/fake/file.mock")
        assert result.parser_used is not None
