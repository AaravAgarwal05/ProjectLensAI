"""ProcessingPipeline — orchestrator for parse -> clean -> metadata extraction.

The pipeline drives a document through three stages with lifecycle hooks at
every boundary.  Each stage is replaceable via dependency injection.

Typical usage::

    pipeline = ProcessingPipeline(
        parser_registry=ParserRegistry(),
        cleaner_pipeline=CleaningPipeline([WhitespaceCleaner(), UnicodeCleaner()]),
        metadata_extractor=MetadataExtractor(),
        hooks=[LoggingHook(), MetricsHook()],
    )
    doc = await pipeline.run("/path/to/document.pdf")
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from shared.models.processing import (
    DocumentMetadata,
    ParsedDocument,
    ProcessingError,
    ProcessingStatistics,
    ProcessingWarning,
)

from src.document_processing.cleaners.base import CleaningPipeline
from src.document_processing.exceptions import ProcessingError as ProcessingErrorException
from src.document_processing.metadata import MetadataExtractor
from src.document_processing.parsers.registry import ParserRegistry

logger = logging.getLogger(__name__)


# ── ProcessingContext ────────────────────────────────────────────────────────


class ProcessingContext:
    """Mutable runtime state accumulated across pipeline stages.

    A fresh context is created for every ``ProcessingPipeline.run()`` call.
    It is the single point of truth for the current status, warnings, and
    errors produced during processing.
    """

    def __init__(self, file_path: str) -> None:
        self.file_path: str = file_path
        self.parsed_doc: ParsedDocument | None = None
        self.start_time: datetime | None = None
        self.status: str = "idle"
        self.errors: list[ProcessingError] = []
        self.warnings: list[ProcessingWarning] = []

    def add_warning(
        self,
        stage: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record a non-fatal warning for the current processing stage."""
        self.warnings.append(
            ProcessingWarning(
                stage=stage,
                message=message,
                details=details or {},
            ),
        )

    def add_error(
        self,
        stage: str,
        message: str,
        code: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record a fatal error for the current processing stage."""
        self.errors.append(
            ProcessingError(
                stage=stage,
                message=message,
                code=code,
                details=details or {},
            ),
        )

    def elapsed_ms(self) -> float:
        """Milliseconds elapsed since *start_time*, or ``0.0`` if unset."""
        if self.start_time is None:
            return 0.0
        return (datetime.utcnow() - self.start_time).total_seconds() * 1000


# ── PipelineHook ─────────────────────────────────────────────────────────────


class PipelineHook:
    """Lifecycle hooks for the processing pipeline.

    Subclass and override only the methods you care about.  All methods have
    default no-op implementations so that partial implementations compose
    safely in a hook list.
    """

    def on_before_parse(self, ctx: ProcessingContext) -> None:
        """Called immediately before the parse stage."""

    def on_after_parse(self, ctx: ProcessingContext) -> None:
        """Called immediately after the parse stage completes successfully."""

    def on_before_clean(self, ctx: ProcessingContext) -> None:
        """Called immediately before the clean stage."""

    def on_after_clean(self, ctx: ProcessingContext) -> None:
        """Called immediately after the clean stage completes successfully."""

    def on_before_metadata(self, ctx: ProcessingContext) -> None:
        """Called immediately before the metadata-extraction stage."""

    def on_after_metadata(self, ctx: ProcessingContext) -> None:
        """Called immediately after the metadata-extraction stage completes."""

    def on_error(self, ctx: ProcessingContext, error: Exception) -> None:
        """Called when any stage raises an unhandled exception.

        The pipeline will re-raise the exception as a ``ProcessingError``
        after all hooks have been notified.
        """

    def on_complete(self, ctx: ProcessingContext) -> None:
        """Called after the pipeline finishes successfully and all statistics
        have been populated."""


# ── ProcessingPipeline ───────────────────────────────────────────────────────


class ProcessingPipeline:
    """Orchestrator that drives parse -> clean -> metadata extraction.

    Stateless -- a fresh ``ProcessingContext`` is created for each
    ``run()`` call.  All dependencies are injected at construction time.

    Parameters
    ----------
    parser_registry:
        Registry used to resolve a parser for the input file format.
    cleaner_pipeline:
        Optional composite cleaner applied after parsing.  If ``None`` the
        clean stage is skipped and ``clean_text`` is set from ``raw_text``.
    metadata_extractor:
        Optional metadata extractor.  Defaults to a fresh ``MetadataExtractor``.
    hooks:
        Optional list of lifecycle hooks invoked at each stage boundary.
    """

    def __init__(
        self,
        parser_registry: ParserRegistry,
        cleaner_pipeline: CleaningPipeline | None = None,
        metadata_extractor: MetadataExtractor | None = None,
        hooks: list[PipelineHook] | None = None,
    ) -> None:
        self._parser_registry = parser_registry
        self._cleaner_pipeline = cleaner_pipeline
        self._metadata_extractor = metadata_extractor or MetadataExtractor()
        self._hooks: list[PipelineHook] = list(hooks) if hooks else []

    def register_hook(self, hook: PipelineHook) -> None:
        """Append *hook* to the lifecycle hook list.

        Hooks are invoked in registration order.  Adding hooks after
        ``run()`` has started is safe — each call creates its own context.
        """
        self._hooks.append(hook)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(self, file_path: str) -> ParsedDocument:
        """Execute the full pipeline on *file_path*.

        Stages
            parse  ->  clean  ->  metadata extraction  ->  finalize

        Returns a fully-populated ``ParsedDocument`` with
        ``ProcessingStatistics`` attached.

        Raises
        ------
        ProcessingErrorException
            Wraps any exception raised during pipeline execution.  The
            original exception is chained via ``__cause__``.
        """
        ctx = ProcessingContext(file_path=file_path)
        ctx.start_time = datetime.utcnow()
        ctx.status = "parsing"

        extension = Path(file_path).suffix.lstrip(".").lower()

        try:
            # ── Stage 1: Parse ────────────────────────────────────────────
            parser = self._parser_registry.get(extension)
            self._fire("on_before_parse", ctx)

            t0 = time.perf_counter()
            parsed_doc = await parser.parse(file_path)
            parse_time_ms = (time.perf_counter() - t0) * 1000

            parsed_doc.parser_used = parser.name
            ctx.parsed_doc = parsed_doc
            self._fire("on_after_parse", ctx)

            # ── Stage 2: Clean ────────────────────────────────────────────
            if self._cleaner_pipeline is not None:
                ctx.status = "cleaning"
                self._fire("on_before_clean", ctx)

                t0 = time.perf_counter()
                cleaned_text = self._cleaner_pipeline.run(parsed_doc.raw_text)
                clean_time_ms = (time.perf_counter() - t0) * 1000

                parsed_doc.clean_text = cleaned_text
                self._fire("on_after_clean", ctx)
            else:
                clean_time_ms = 0.0
                if not parsed_doc.clean_text:
                    parsed_doc.clean_text = parsed_doc.raw_text

            # ── Stage 3: Metadata ─────────────────────────────────────────
            ctx.status = "metadata"
            self._fire("on_before_metadata", ctx)

            t0 = time.perf_counter()
            metadata = self._metadata_extractor.extract(
                file_path=file_path,
                content=parsed_doc.clean_text,
                parser_metadata=_doc_metadata_to_dict(parsed_doc.metadata),
            )
            metadata_time_ms = (time.perf_counter() - t0) * 1000

            parsed_doc.metadata = metadata
            self._fire("on_after_metadata", ctx)

            # ── Stage 4: Finalize ─────────────────────────────────────────
            parsed_doc.statistics = ProcessingStatistics(
                parse_time_ms=parse_time_ms,
                clean_time_ms=clean_time_ms,
                metadata_time_ms=metadata_time_ms,
                total_time_ms=ctx.elapsed_ms(),
                page_count=len(parsed_doc.pages),
                raw_char_count=len(parsed_doc.raw_text),
                clean_char_count=len(parsed_doc.clean_text),
            )
            ctx.status = "completed"

            self._fire("on_complete", ctx)

            return parsed_doc

        except Exception as exc:
            ctx.status = "error"
            ctx.add_error(
                stage=ctx.status if ctx.status not in ("idle",) else "unknown",
                message=str(exc),
                code=getattr(exc, "code", "pipeline_error"),
            )
            self._fire("on_error", ctx, exc)
            raise ProcessingErrorException(
                message=f"Pipeline failed for {file_path}: {exc}",
                code=getattr(exc, "code", "pipeline_error"),
                details={"file_path": file_path, "stage": ctx.status},
            ) from exc

    # ── internal helpers ──────────────────────────────────────────────────

    def _fire(self, method_name: str, ctx: ProcessingContext, *args: Any) -> None:
        """Invoke *method_name* on every registered hook.

        Failures in hooks are logged but never propagated — a broken hook
        must not interrupt the pipeline.
        """
        for hook in self._hooks:
            try:
                getattr(hook, method_name)(ctx, *args)
            except Exception:
                logger.exception(
                    "Hook %s.%s raised an exception and was suppressed",
                    type(hook).__name__,
                    method_name,
                )


# ── helpers ─────────────────────────────────────────────────────────────────


def _doc_metadata_to_dict(metadata: DocumentMetadata) -> dict[str, Any]:
    """Convert a ``DocumentMetadata`` pydantic model to a flat dict.

    This is passed as ``parser_metadata`` to ``MetadataExtractor.extract``
    so that metadata already discovered by the parser (e.g. author, title
    from PDF metadata) can override auto-derived values.
    """
    raw = metadata.model_dump()
    # Drop fields that are not meaningful as parser overrides.
    raw.pop("extra", None)
    return raw
