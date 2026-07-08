"""Tests for ProcessingService — orchestrates background document processing."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.processing import ParsedDocument, ProcessingStatistics
from src.document_processing.lifecycle import STATUS_FAILED, STATUS_PROCESSING, STATUS_READY
from src.document_processing.pipeline import ProcessingPipeline
from src.services.processing_service import ProcessingService
from src.storage.base import StorageProvider

from .conftest import make_report


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_pipeline() -> AsyncMock:
    """Mock ProcessingPipeline that returns a simple ParsedDocument."""
    pipeline = AsyncMock(spec=ProcessingPipeline)
    pipeline.run.return_value = ParsedDocument(
        parser_used="mock",
        raw_text="content",
        clean_text="content",
        statistics=ProcessingStatistics(
            parse_time_ms=10,
            clean_time_ms=5,
            metadata_time_ms=3,
            total_time_ms=18,
            page_count=1,
            raw_char_count=7,
            clean_char_count=7,
        ),
    )
    return pipeline


@pytest.fixture
def mock_storage() -> AsyncMock:
    """Mock StorageProvider."""
    storage = AsyncMock(spec=StorageProvider)
    storage.retrieve.return_value = b"file content"
    return storage


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Return an AsyncMock session that supports the async context manager protocol."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    return session


def _make_mock_repo(report, status_updates: list[str]):
    """Build a mock ReportRepository that captures status updates."""
    mock_repo = MagicMock()
    mock_repo.get = AsyncMock(return_value=report)

    async def _tracking_update(_id: object, **kwargs: object) -> None:
        if "status" in kwargs:
            status_updates.append(str(kwargs["status"]))

    mock_repo.update = _tracking_update
    return mock_repo


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestProcessingService:
    """Suite for ProcessingService."""

    @pytest.mark.asyncio
    async def test_process_report_success(
        self,
        mock_pipeline: AsyncMock,
        mock_storage: AsyncMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """A successful processing run returns without raising, the pipeline is
        called, and the report transitions through processing/ready states."""
        report_id = uuid4()
        report = make_report(id=report_id, storage_path="reports/test/test.pdf",
                             original_filename="test.pdf")

        status_updates: list[str] = []
        mock_repo = _make_mock_repo(report, status_updates)

        # Patch ReportRepository in BOTH modules that import it
        with (
            patch("src.services.processing_service.ReportRepository",
                  return_value=mock_repo) as _,
            patch("src.document_processing.lifecycle.ReportRepository",
                  return_value=mock_repo) as _,
        ):
            def _db_factory() -> AsyncSession:
                return mock_db_session

            service = ProcessingService(
                pipeline=mock_pipeline,
                storage=mock_storage,
                db_factory=_db_factory,
            )

            await service.process_report(report_id)

            # Pipeline was invoked
            mock_pipeline.run.assert_awaited_once()

            # Report was loaded
            mock_repo.get.assert_awaited_once_with(report_id)

            # Status transitions: processing then ready
            assert STATUS_PROCESSING in status_updates
            assert STATUS_READY in status_updates

    @pytest.mark.asyncio
    async def test_process_report_sets_failed_on_error(
        self,
        mock_storage: AsyncMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """When the pipeline raises, the report is marked as failed."""
        report_id = uuid4()
        report = make_report(id=report_id, storage_path="reports/test/test.pdf",
                             original_filename="test.pdf")

        pipeline = AsyncMock(spec=ProcessingPipeline)
        pipeline.run.side_effect = RuntimeError("processing failure")

        status_updates: list[str] = []
        mock_repo = _make_mock_repo(report, status_updates)

        with (
            patch("src.services.processing_service.ReportRepository",
                  return_value=mock_repo) as _,
            patch("src.document_processing.lifecycle.ReportRepository",
                  return_value=mock_repo) as _,
        ):
            def _db_factory() -> AsyncSession:
                return mock_db_session

            service = ProcessingService(
                pipeline=pipeline,
                storage=mock_storage,
                db_factory=_db_factory,
            )

            # Should not raise — process_report swallows exceptions
            await service.process_report(report_id)

            assert STATUS_FAILED in status_updates

    @pytest.mark.asyncio
    async def test_process_report_missing_report(
        self,
        mock_pipeline: AsyncMock,
        mock_storage: AsyncMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """When the report is not found, process_report returns early."""
        report_id = uuid4()

        with patch(
            "src.services.processing_service.ReportRepository",
        ) as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get = AsyncMock(return_value=None)  # report not found
            mock_repo_cls.return_value = mock_repo

            def _db_factory() -> AsyncSession:
                return mock_db_session

            service = ProcessingService(
                pipeline=mock_pipeline,
                storage=mock_storage,
                db_factory=_db_factory,
            )

            await service.process_report(report_id)

            # Pipeline should NOT be called since the report was not found
            mock_pipeline.run.assert_not_called()
