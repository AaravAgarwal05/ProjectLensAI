"""Background processing service for reports.

ProcessingService coordinates the document processing pipeline with
storage and database operations, designed to run as a FastAPI
``BackgroundTask`` after the upload response has been sent.

Usage
-----
::

    service = ProcessingService(
        pipeline=processing_pipeline,
        storage=storage_provider,
        db_factory=async_session_factory,
    )
    await service.process_report(report_id)   # typically via BackgroundTasks
"""

from __future__ import annotations

import logging
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.document_processing.lifecycle import (
    STATUS_FAILED,
    STATUS_PROCESSING,
    STATUS_READY,
    update_report_status,
)
from src.document_processing.pipeline import ProcessingPipeline
from src.repository.report import ReportRepository
from src.storage.base import StorageProvider

logger = logging.getLogger(__name__)

# ── Helper: log a step with clear layman label ───────────────────────────────

_STEP = 0


def _log_step(msg: str, *args: object) -> None:
    """Print a step marker so logs are easy to scan."""
    global _STEP  # noqa: PLW0603
    _STEP += 1
    if args:
        logger.info("═► STEP %d: " + msg, _STEP, *args)
    else:
        logger.info("═► STEP %d: %s", _STEP, msg)


def _log_ok(msg: str, *args: object) -> None:
    """Log a success message — msg may contain fmt placeholders filled by args."""
    if args:
        logger.info("  ✔ " + msg, *args)
    else:
        logger.info("  ✔ " + msg)


def _log_fail(msg: str, *args: object) -> None:
    """Log a failure message — msg may contain fmt placeholders filled by args."""
    if args:
        logger.error("  ✘ " + msg, *args)
    else:
        logger.error("  ✘ " + msg)


# ── ProcessingService ─────────────────────────────────────────────────────────


class ProcessingService:
    """Orchestrates background document processing for a report.

    All external dependencies are injected at construction time so the
    service is fully testable without real storage or a database.

    Parameters
    ----------
    pipeline:
        The ``ProcessingPipeline`` that drives parse -> clean -> metadata
        extraction.
    storage:
        ``StorageProvider`` used to download the report file from the
        configured backend.
    db_factory:
        A no-argument callable that returns a new ``AsyncSession``.
        Typically ``async_session_factory`` from ``src.database.session``.
    """

    def __init__(
        self,
        pipeline: ProcessingPipeline,
        storage: StorageProvider,
        db_factory: Callable[[], AsyncSession],
    ) -> None:
        self._pipeline = pipeline
        self._storage = storage
        self._db_factory = db_factory

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def process_report(
        self,
        report_id: UUID,
        user_id: str | None = None,
        preferences: dict | None = None,
    ) -> None:
        """Execute the full processing lifecycle for *report_id*.

        Steps
        -----
        1. Open a new database session and load the report.
        2. Set the report status to ``processing``.
        3. Download the report file from storage to a temporary location.
        4. Run ``ProcessingPipeline.run(tmp_path)``.
        5. Chunk and embed the parsed document using user preferences (if available).
        6. On success, update the report status to ``ready``.
        7. On failure, update the report status to ``failed``.
        8. Clean up the temporary file in all cases.

        Exceptions are logged and swallowed -- this method is designed to
        run in a background task and must not crash the request handler.
        """
        # Reset step counter so each run starts from 1
        global _STEP  # noqa: PLW0603
        _STEP = 0

        tmp_path: str | None = None
        parsed_doc = None
        filename = "unknown"
        try:
            # ── Step 1-2: Load report & mark as processing ────────────────
            _log_step("Loading report from database and marking it as 'processing'...")
            async with self._db_factory() as session:
                repo = ReportRepository(session)
                report = await repo.get(report_id)
                if report is None:
                    _log_fail("Report %s not found in database. Cannot process.", report_id)
                    logger.info("  └── This means the report was deleted or never created.")
                    return

                filename = report.original_filename or "unknown"
                _log_ok("Found report '%s' (ID: %s)", filename, report_id)

                await repo.update(report_id, status=STATUS_PROCESSING)
                await session.commit()
                _log_ok("Report status set to 'processing'. The UI should show a spinner now.")

                # Load user preferences if needed
                if user_id and preferences is None:
                    _log_step("Loading your processing preferences...")
                    from src.database.models.user import User

                    result = await session.execute(select(User).where(User.id == user_id))
                    user = result.scalar_one_or_none()
                    if user is not None:
                        preferences = getattr(user, "preferences", None)
                        _log_ok("Loaded preferences: %s", preferences)
                    else:
                        logger.info("  └── User not found, using default settings.")

            # ── Step 3: Download file ──────────────────────────────────────
            _log_step("Downloading the uploaded file from storage...")
            if not report.storage_path:
                _log_fail(
                    "No storage path for report. "
                    "The file was probably not saved correctly during upload."
                )
                async with self._db_factory() as session:
                    await update_report_status(session, report_id, STATUS_FAILED)
                    await session.commit()
                return

            content = await self._storage.retrieve(report.storage_path)
            _log_ok("Downloaded %d bytes for file '%s'", len(content), filename)

            ext = (
                Path(report.original_filename).suffix
                if report.original_filename
                else ".tmp"
            )
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            tmp_path = tmp.name
            tmp.write(content)
            tmp.close()
            _log_ok("Saved temporary copy to: %s", tmp_path)

            # ── Step 4: Run processing pipeline (parse → clean → metadata) ─
            _log_step(
                "Reading the document — extracting text, cleaning, and detecting metadata..."
            )
            logger.info(
                "  └── This may take a while depending on file size. "
                "PDFs with many pages take longer."
            )
            parsed_doc = await self._pipeline.run(tmp_path)

            if parsed_doc:
                _log_ok(
                    "Document read successfully! Parser used: %s",
                    parsed_doc.parser_used,
                )
                logger.info(
                    "  ├── Pages found: %d",
                    parsed_doc.statistics.page_count,
                )
                logger.info(
                    "  ├── Characters extracted: %d",
                    parsed_doc.statistics.raw_char_count,
                )
                logger.info(
                    "  └── Clean characters: %d",
                    parsed_doc.statistics.clean_char_count,
                )
            else:
                _log_fail("Pipeline returned no document. Nothing to process.")
                raise RuntimeError("Empty pipeline result")

            # ── Step 5: Chunk + embed ─────────────────────────────────────
            chunking_strategy = "heading_aware"
            embedding_provider = "gemini"
            if preferences and isinstance(preferences, dict):
                chunking_strategy = preferences.get("chunking_strategy", chunking_strategy)
                embedding_provider = preferences.get("embedding_provider", embedding_provider)
                _log_step(
                    "Using your settings: chunking='%s', embedding='%s'",
                    chunking_strategy,
                    embedding_provider,
                )
            else:
                _log_step(
                    "Using default settings: chunking='%s', embedding='%s'",
                    chunking_strategy,
                    embedding_provider,
                )

            if parsed_doc and parsed_doc.clean_text:
                await self._index_document(
                    report_id=report_id,
                    parsed_doc=parsed_doc,
                    chunking_strategy=chunking_strategy,
                    embedding_provider=embedding_provider,
                    original_filename=filename,
                    preferences=preferences,
                )
            else:
                logger.info(
                    "  └── No clean text found — skipping chunking and embedding. "
                    "The document may be empty or image-only."
                )

            # ── Step 6: Mark as ready ─────────────────────────────────────
            _log_step("All done! Marking report as 'ready'...")
            async with self._db_factory() as session:
                await update_report_status(session, report_id, STATUS_READY)
                await session.commit()

            _log_ok(
                "Report '%s' is ready! You can now view it in the reports list.",
                filename,
            )
            logger.info(
                "  └── Parser: %s | Pages: %d | Chars: %d",
                parsed_doc.parser_used,
                parsed_doc.statistics.page_count,
                parsed_doc.statistics.raw_char_count,
            )

        except Exception as exc:
            # ── Step 7: Mark as failed ────────────────────────────────────
            _log_fail(
                "Something went wrong while processing '%s'.",
                filename,
            )
            logger.error("  └── Error details: %s", exc)
            logger.info(
                "  └── The report has been marked as 'failed'. "
                "You can try uploading it again."
            )
            try:
                async with self._db_factory() as session:
                    await update_report_status(session, report_id, STATUS_FAILED)
                    await session.commit()
                _log_ok("Report status updated to 'failed' in database.")
            except Exception as db_err:
                logger.error("  └── Could not update status either: %s", db_err)

        finally:
            # ── Step 8: Clean up ──────────────────────────────────────────
            if tmp_path is not None and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                    logger.debug("Deleted temp file %s", tmp_path)
                except OSError:
                    logger.warning("Could not delete temp file %s", tmp_path)

    async def _index_document(
        self,
        report_id: UUID,
        parsed_doc,
        chunking_strategy: str,
        embedding_provider: str,
        original_filename: str,
        preferences: dict | None = None,
    ) -> None:
        """Chunk and embed a parsed document, then index in vector store.

        Uses the user's chosen chunking strategy and embedding provider.
        Failures are logged but never raised -- indexing is best-effort
        and must not block the report from being marked ``ready``.
        """
        try:
            # ── Chunking ──────────────────────────────────────────────────
            _log_step(
                "Splitting the document into smaller pieces (chunking) using '%s' strategy...",
                chunking_strategy,
            )
            strategy_names = {
                "fixed": "Standard (fixed-size chunks)",
                "heading_aware": "Precise (section-aware chunks)",
                "recursive": "Deep (recursive splitting)",
            }
            logger.info(
                "  └── You chose: %s",
                strategy_names.get(chunking_strategy, chunking_strategy),
            )

            from src.ai_core.chunking.configuration import ChunkingConfiguration
            from src.ai_core.chunking.factory import ChunkingFactory
            from src.ai_core.chunking.pipeline import ChunkingPipeline
            from src.ai_core.chunking.registry import ChunkingRegistry

            registry = ChunkingRegistry()
            from src.ai_core.chunking.strategies.fixed import FixedChunker
            from src.ai_core.chunking.strategies.heading_aware import HeadingAwareChunker
            from src.ai_core.chunking.strategies.recursive import RecursiveChunker

            registry.register("fixed", FixedChunker)
            registry.register("recursive", RecursiveChunker)
            registry.register("heading_aware", HeadingAwareChunker)

            # Build config overrides from user preferences
            chunk_config_overrides: dict[str, object] = {}
            if preferences and isinstance(preferences, dict):
                for key in ("chunk_size", "chunk_overlap", "min_chunk_size"):
                    if key in preferences:
                        chunk_config_overrides[key] = preferences[key]

            factory = ChunkingFactory(registry)
            chunk_pipeline = ChunkingPipeline(factory=factory)
            chunk_result = chunk_pipeline.run(
                parsed_doc,
                strategy=chunking_strategy,
                config=ChunkingConfiguration(**chunk_config_overrides),
            )

            if not chunk_result.successful or not chunk_result.chunks:
                _log_fail(
                    "Could not split document into pieces. "
                    "Strategy: %s, Errors: %s",
                    chunking_strategy,
                    chunk_result.errors or "no chunks produced",
                )
                return

            _log_ok(
                "Document split into %d pieces (chunks).",
                len(chunk_result.chunks),
            )
            avg_len = sum(len(c.text) for c in chunk_result.chunks) / len(chunk_result.chunks)
            logger.info(
                "  ├── Each piece is roughly %d characters long on average.",
                int(avg_len),
            )
            logger.info(
                "  └── These pieces will now be converted to searchable numbers (embeddings)."
            )

            # ── Embedding ─────────────────────────────────────────────────
            _log_step(
                "Converting text pieces into searchable numbers (embeddings) using '%s'...",
                embedding_provider,
            )
            provider_names = {
                "sentence_transformer": "Local (on-device, no internet needed)",
                "ollama": "Cloud (via Ollama server)",
                "gemini": "Cloud (via Google Gemini)",
            }
            logger.info(
                "  └── You chose: %s",
                provider_names.get(embedding_provider, embedding_provider),
            )

            from src.ai_core.embedding.factory import (
                EmbeddingFactory,
                default_embedding_registry,
            )
            from src.ai_core.embedding.pipeline import EmbeddingPipeline

            emb_registry = default_embedding_registry()
            emb_factory = EmbeddingFactory(emb_registry)
            embed_pipeline = EmbeddingPipeline(factory=emb_factory)
            embed_result = await embed_pipeline.run(
                chunk_result.chunks,
                provider=embedding_provider,
            )

            if not embed_result.successful or not embed_result.embeddings:
                _log_fail(
                    "Could not convert text to numbers. "
                    "Provider: %s, Errors: %s",
                    embedding_provider,
                    embed_result.errors or "no embeddings produced",
                )
                return

            _log_ok(
                "Successfully converted %d text pieces into number representations.",
                len(embed_result.embeddings),
            )
            logger.info(
                "  └── Each piece is now a vector of %d numbers.",
                embed_result.embeddings[0].dimensions if embed_result.embeddings else 0,
            )

            # ── Index in vector store ─────────────────────────────────────
            _log_step("Saving the number representations to the search database...")
            logger.info(
                "  └── This lets the system quickly find relevant content when you search."
            )

            try:
                from src.ai_core.vector_store.configuration import (
                    VectorStoreConfiguration,
                )
                from src.ai_core.vector_store.factory import VectorStoreFactory
                from src.ai_core.vector_store.indexing import IndexingEngine
                from src.ai_core.vector_store.providers.chroma_store import (
                    ChromaVectorStore,
                )
                from src.ai_core.vector_store.providers.pgvector_store import (
                    PgVectorStore,
                )

                store_factory = VectorStoreFactory()
                store_factory.registry.register("chroma", ChromaVectorStore)
                store_factory.registry.register("pgvector", PgVectorStore)

                from src.config.settings import get_settings

                _s = get_settings()
                store_provider = _s.VECTOR_STORE_PROVIDER
                dims = embed_result.embeddings[0].dimensions if embed_result.embeddings else 384
                if store_provider == "pgvector":
                    extra: dict[str, Any] = {
                        "dsn": _s.DATABASE_URL.replace("+asyncpg", ""),
                        "dimensions": dims,
                    }
                else:
                    extra = {"host": _s.CHROMA_HOST, "port": _s.CHROMA_PORT}
                config = VectorStoreConfiguration(
                    store=store_provider,
                    collection_name=f"report_{report_id}",
                    extra=extra,
                )
                engine = IndexingEngine(factory=store_factory, config=config)
                index_result = await engine.index(embed_result.embeddings)
                if index_result.successful:
                    _log_ok(
                        "All %d entries saved to search database!",
                        len(index_result.documents or []),
                    )
                    logger.info(
                        "  └── The report is now fully searchable."
                    )
                else:
                    _log_fail(
                        "Some entries could not be saved. Errors: %s",
                        index_result.errors,
                    )
            except Exception as idx_err:
                _log_fail(
                    "Could not save to search database: %s",
                    idx_err,
                )
                logger.info(
                    "  └── Don't worry — the report itself is still processed. "
                    "Search will work once the database connection is fixed."
                )

        except Exception as exc:
            _log_fail(
                "The indexing pipeline (chunk → embed → save) hit an error: %s",
                exc,
            )
            logger.info(
                "  └── The report will still be marked as 'ready' but may "
                "not be searchable until this is fixed."
            )
