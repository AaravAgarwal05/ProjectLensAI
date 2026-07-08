"""Lifecycle constants and helpers for report processing status transitions.

Status flow
-----------
``uploaded`` → ``processing`` → ``ready``
                             ↘  ``failed``
"""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.report import ReportRepository

logger = logging.getLogger(__name__)

# ── Processing lifecycle status values ──────────────────────────────────────
# These map to the ``Report.status`` column values used during processing.

STATUS_QUEUED = "uploaded"
"""Report file has been uploaded but not yet processed (initial status)."""

STATUS_PROCESSING = "processing"
"""Document is actively being parsed, cleaned, and analysed."""

STATUS_READY = "ready"
"""Processing completed successfully; the report is available for query."""

STATUS_FAILED = "failed"
"""Processing failed; check the error log for the root cause."""


# ── Status helpers ──────────────────────────────────────────────────────────


async def update_report_status(
    session: AsyncSession,
    report_id: UUID,
    status: str,
) -> None:
    """Transition a report to *status*.

    Args:
        session: Open database session (caller is responsible for commit).
        report_id: UUID of the report to update.
        status: Target status (use ``STATUS_*`` constants).
    """
    repo = ReportRepository(session)
    await repo.update(report_id, status=status)


async def handle_processing_error(
    session: AsyncSession,
    report_id: UUID,
    error: Exception,
) -> None:
    """Mark a report as ``failed`` and log the error.

    Args:
        session: Open database session (caller is responsible for commit).
        report_id: UUID of the failed report.
        error: The exception that caused the failure.
    """
    logger.error("Processing failed for report %s: %s", report_id, error)
    repo = ReportRepository(session)
    await repo.update(report_id, status=STATUS_FAILED)
