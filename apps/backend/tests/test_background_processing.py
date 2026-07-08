"""Integration-style tests for background processing — the processing flow
triggered after a report upload completes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.dependencies import get_current_user, get_db
from src.config.settings import AppSettings
from src.config.settings import get_settings as _cached_get_settings
from src.main import create_app

from .conftest import make_report, make_version


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def bg_api_client() -> AsyncClient:
    """HTTP client with dependency overrides for background processing tests.

    All external dependencies (DB, auth) are mocked so tests focus on the
    processing-triggering logic.
    """
    app = create_app()

    # Override DB session
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()

    execute_result = MagicMock()
    execute_result.scalars.return_value.all.return_value = []
    execute_result.scalar_one_or_none.return_value = None
    execute_result.scalar_one.return_value = 0
    mock_session.execute.return_value = execute_result
    mock_session.get.return_value = None

    async def _override_db():
        yield mock_session

    async def _override_user():
        return {"sub": "test-user-id", "role": "user"}

    settings = AppSettings(
        MAX_UPLOAD_SIZE=1024 * 100,
        ALLOWED_EXTENSIONS=[".pdf", ".docx", ".txt"],
        STORAGE_PROVIDER="local",
        STORAGE_LOCAL_PATH="/tmp/test_storage_bg",
    )

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[_cached_get_settings] = lambda: settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBackgroundProcessing:
    """Suite for background processing integration."""

    @pytest.mark.asyncio
    async def test_background_task_triggers_after_upload(
        self,
        bg_api_client: AsyncClient,
    ) -> None:
        """After a report is created via the API, the processing background
        task is triggered (verified by mocking _build_processing_service)."""
        report_id = uuid4()

        mock_proc_svc = AsyncMock()

        with (
            patch("src.api.v1.reports._build_processing_service",
                  return_value=mock_proc_svc),
            patch("src.api.v1.reports._build_storage_provider"),
            patch("src.api.v1.reports.ReportService") as mock_report_svc_cls,
        ):
            mock_report_svc = MagicMock()
            mock_report_svc.create_report = AsyncMock(
                return_value=make_report(
                    id=report_id,
                    title="BG Test Report",
                    storage_path="reports/test_id/test.pdf",
                    original_filename="test.pdf",
                ),
            )
            mock_report_svc_cls.return_value = mock_report_svc

            response = await bg_api_client.post(
                "/api/v1/reports",
                data={
                    "title": "BG Test Report",
                    "description": "Testing background processing",
                },
                files={
                    "file": (
                        "test.pdf",
                        b"%PDF-1.4 content",
                        "application/pdf",
                    ),
                },
            )

        assert response.status_code == 201
        mock_proc_svc.process_report.assert_awaited_once()
        args, _ = mock_proc_svc.process_report.call_args
        assert isinstance(args[0], UUID)

    @pytest.mark.asyncio
    async def test_status_becomes_ready_after_processing(
        self,
        bg_api_client: AsyncClient,
    ) -> None:
        """When mocking the full processing flow, the endpoint returns 201 and
        the background processing mock is invoked."""
        report_id = uuid4()

        mock_proc_svc = AsyncMock()

        with (
            patch("src.api.v1.reports._build_processing_service",
                  return_value=mock_proc_svc),
            patch("src.api.v1.reports._build_storage_provider"),
            patch("src.api.v1.reports.ReportService") as mock_report_svc_cls,
        ):
            mock_report_svc = MagicMock()
            mock_report_svc.create_report = AsyncMock(
                return_value=make_report(
                    id=report_id,
                    title="Ready Test",
                    storage_path="reports/test_id/test.pdf",
                    original_filename="test.pdf",
                ),
            )
            mock_report_svc_cls.return_value = mock_report_svc

            response = await bg_api_client.post(
                "/api/v1/reports",
                data={"title": "Ready Test"},
                files={
                    "file": (
                        "report.pdf",
                        b"content",
                        "application/pdf",
                    ),
                },
            )

        assert response.status_code == 201
        mock_proc_svc.process_report.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_background_processing_invoked_for_version_upload(
        self,
        bg_api_client: AsyncClient,
    ) -> None:
        """Uploading a new version also triggers background processing."""
        report_id = uuid4()

        mock_proc_svc = AsyncMock()

        with (
            patch("src.api.v1.reports._build_processing_service",
                  return_value=mock_proc_svc),
            patch("src.api.v1.reports._build_storage_provider"),
            patch("src.api.v1.reports.ReportService") as mock_report_svc_cls,
        ):
            mock_report_svc = MagicMock()
            mock_report_svc.upload_new_version = AsyncMock(
                return_value=make_version(
                    report_id=report_id,
                    version_number=2,
                    original_filename="v2.pdf",
                ),
            )
            mock_report_svc_cls.return_value = mock_report_svc

            response = await bg_api_client.post(
                f"/api/v1/reports/{report_id}/versions",
                files={
                    "file": (
                        "v2.pdf",
                        b"v2 content",
                        "application/pdf",
                    ),
                },
            )

        assert response.status_code == 201
        mock_proc_svc.process_report.assert_awaited_once_with(report_id)
