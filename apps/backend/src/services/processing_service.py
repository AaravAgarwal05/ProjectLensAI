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
from uuid import UUID

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

    async def process_report(self, report_id: UUID) -> None:
        """Execute the full processing lifecycle for *report_id*.

        Steps
        -----
        1. Open a new database session and load the report.
        2. Set the report status to ``processing``.
        3. Download the report file from storage to a temporary location.
        4. Run ``ProcessingPipeline.run(tmp_path)``.
        5. On success, update the report status to ``ready``.
        6. On failure, update the report status to ``failed``.
        7. Clean up the temporary file in all cases.

        Exceptions are logged and swallowed -- this method is designed to
        run in a background task and must not crash the request handler.
        """
        tmp_path: str | None = None
        try:
            # 1 & 2: Load report, mark as processing
            async with self._db_factory() as session:
                repo = ReportRepository(session)
                report = await repo.get(report_id)
                if report is None:
                    logger.error("Report %s not found -- skipping processing", report_id)
                    return

                await repo.update(report_id, status=STATUS_PROCESSING)
                await session.commit()

            # 3: Download the stored file to a temp location
            if not report.storage_path:
                logger.error("Report %s has no storage path -- cannot process", report_id)
                async with self._db_factory() as session:
                    await update_report_status(session, report_id, STATUS_FAILED)
                    await session.commit()
                return

            content = await self._storage.retrieve(report.storage_path)

            ext = (
                Path(report.original_filename).suffix
                if report.original_filename
                else ".tmp"
            )
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            tmp_path = tmp.name
            tmp.write(content)
            tmp.close()

            # 4: Run the processing pipeline
            logger.info(
                "Processing report %s (file=%s)",
                report_id,
                report.original_filename,
            )
            parsed_doc = await self._pipeline.run(tmp_path)

            # 5: Mark as ready
            async with self._db_factory() as session:
                await update_report_status(session, report_id, STATUS_READY)
                await session.commit()

            logger.info(
                "Report %s processed successfully "
                "(parser=%s, pages=%d, chars=%d)",
                report_id,
                parsed_doc.parser_used,
                parsed_doc.statistics.page_count,
                parsed_doc.statistics.raw_char_count,
            )

        except Exception as exc:
            # 6: Mark as failed
            logger.exception("Processing failed for report %s: %s", report_id, exc)
            try:
                async with self._db_factory() as session:
                    await update_report_status(session, report_id, STATUS_FAILED)
                    await session.commit()
            except Exception as db_err:
                logger.error(
                    "Failed to update report %s status to failed: %s",
                    report_id,
                    db_err,
                )

        finally:
            # 7: Clean up temp file
            if tmp_path is not None and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    logger.warning("Failed to remove temp file %s", tmp_path)
