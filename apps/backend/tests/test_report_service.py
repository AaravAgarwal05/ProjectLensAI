"""Tests for :class:`ReportService` — business logic and validation.

Repositories and storage are mocked so that only the service-layer
orchestration, validation rules, and error handling are exercised.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, call
from uuid import uuid4

import pytest
from fastapi import UploadFile

from src.api.exceptions import ProjectLensError
from src.database.models import Report, ReportVersion
from src.repository.report import ReportRepository
from src.repository.version import VersionRepository
from src.services.report_service import ReportService

from .conftest import make_report, make_version


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_file(
    filename: str = "test.pdf",
    content: bytes = b"mock pdf content",
    content_type: str = "application/pdf",
    size: int | None = 999,
) -> MagicMock:
    """Build a fake ``UploadFile`` for service method calls."""
    f: MagicMock = MagicMock(spec=UploadFile)
    f.filename = filename
    f.content_type = content_type
    f.size = size
    f.read = AsyncMock(return_value=content)
    return f


async def _patch_repos(
    service: ReportService,
    report_repo: AsyncMock | None = None,
    version_repo: AsyncMock | None = None,
) -> None:
    """Replace the service's internal repositories with mocks."""
    service._report_repo = report_repo or AsyncMock(spec=ReportRepository)
    service._version_repo = version_repo or AsyncMock(spec=VersionRepository)


# ===================================================================
# File validation
# ===================================================================


class TestValidateFile:
    """``ReportService._validate_file``"""

    async def test_accepts_allowed_extension(self, report_service: ReportService) -> None:
        f = _mock_file(filename="document.pdf")
        # Should not raise
        report_service._validate_file(f)

    async def test_rejects_disallowed_extension(self, report_service: ReportService) -> None:
        f = _mock_file(filename="script.exe")
        with pytest.raises(ProjectLensError) as exc_info:
            report_service._validate_file(f)
        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "invalid_file_extension"

    async def test_rejects_oversized_file(self, report_service: ReportService) -> None:
        f = _mock_file(filename="big.pdf", size=10 * 1024 * 1024)  # 10 MiB >> 100 KiB
        with pytest.raises(ProjectLensError) as exc_info:
            report_service._validate_file(f)
        assert exc_info.value.status_code == 413
        assert exc_info.value.code == "file_too_large"

    async def test_skips_size_check_when_size_is_none(self, report_service: ReportService) -> None:
        f = _mock_file(filename="report.pdf", size=None)
        report_service._validate_file(f)  # should not raise


# ===================================================================
# Create
# ===================================================================


class TestCreateReport:
    """``ReportService.create_report``"""

    async def test_full_flow_creates_report_and_version(
        self,
        report_service: ReportService,
        mock_storage: AsyncMock,
    ) -> None:
        """Happy path: valid file creates a Report + Version, stores content."""
        report_id = uuid4()
        expected_report = make_report(id=report_id)
        expected_version = make_version(report_id=report_id, version_number=1)

        await _patch_repos(report_service)
        report_service._report_repo.create.return_value = expected_report  # type: ignore[attr-defined]
        report_service._version_repo.create.return_value = expected_version  # type: ignore[attr-defined]

        f = _mock_file()
        result = await report_service.create_report(
            file=f,
            title="Annual Report",
            description="Full year review",
            department="Finance",
            author="Jane Doe",
            tags=["finance", "annual"],
            visibility="internal",
            year=2025,
        )

        assert result is expected_report
        assert result.id == report_id

        # File was read
        f.read.assert_awaited_once()

        # Content was stored
        mock_storage.store.assert_awaited_once()
        store_path: str = mock_storage.store.call_args[0][0]
        assert store_path.startswith("reports/")
        assert store_path.endswith("/test.pdf")

        # Report was created with correct metadata
        report_service._report_repo.create.assert_awaited_once_with(
            title="Annual Report",
            description="Full year review",
            department="Finance",
            author="Jane Doe",
            tags=["finance", "annual"],
            visibility="internal",
            year=2025,
            status="uploaded",
            storage_provider="supabase",
            storage_path=store_path,
            original_filename="test.pdf",
            mime_type="application/pdf",
            checksum=report_service._compute_checksum(b"mock pdf content"),
            file_size=16,
        )

        # Version was created for v1
        report_service._version_repo.create.assert_awaited_once_with(
            report_id=report_id,
            version_number=1,
            storage_path=store_path,
            original_filename="test.pdf",
            mime_type="application/pdf",
            checksum=report_service._compute_checksum(b"mock pdf content"),
            file_size=16,
        )

    async def test_raises_on_invalid_extension(self, report_service: ReportService) -> None:
        await _patch_repos(report_service)
        f = _mock_file(filename="virus.exe")
        with pytest.raises(ProjectLensError) as exc_info:
            await report_service.create_report(file=f, title="Bad")
        assert exc_info.value.code == "invalid_file_extension"
        # Repository methods should NOT have been called
        report_service._report_repo.create.assert_not_called()  # type: ignore[attr-defined]

    async def test_raises_on_oversized_file(self, report_service: ReportService) -> None:
        await _patch_repos(report_service)
        f = _mock_file(filename="huge.pdf", size=5 * 1024 * 1024)
        with pytest.raises(ProjectLensError) as exc_info:
            await report_service.create_report(file=f, title="Huge")
        assert exc_info.value.code == "file_too_large"
        report_service._report_repo.create.assert_not_called()  # type: ignore[attr-defined]


# ===================================================================
# Read
# ===================================================================


class TestGetReport:
    """``ReportService.get_report``"""

    async def test_returns_report(self, report_service: ReportService) -> None:
        expected = make_report()
        await _patch_repos(report_service)
        report_service._report_repo.get.return_value = expected  # type: ignore[attr-defined]

        result = await report_service.get_report(expected.id)
        assert result is expected

    async def test_returns_none_when_not_found(self, report_service: ReportService) -> None:
        await _patch_repos(report_service)
        report_service._report_repo.get.return_value = None  # type: ignore[attr-defined]
        result = await report_service.get_report(uuid4())
        assert result is None


class TestListReports:
    """``ReportService.list_reports`` — uses ``self._session.execute`` directly."""

    async def test_returns_paginated_results(self, report_service: ReportService, mock_session: AsyncMock) -> None:
        reports = [make_report(title="R1"), make_report(title="R2")]

        # mock_session is used directly by list_reports — two execute calls.
        # Result objects are MagicMock (not AsyncMock) because their methods
        # (scalar_one, scalars().all) are synchronous SQLAlchemy calls.
        count_mock = MagicMock()
        count_mock.scalar_one.return_value = 2
        fetch_mock = MagicMock()
        fetch_mock.scalars.return_value.all.return_value = reports
        mock_session.execute.side_effect = [count_mock, fetch_mock]

        result, total = await report_service.list_reports(skip=0, limit=20)

        assert list(result) == reports
        assert total == 2

    async def test_filters_by_status(self, report_service: ReportService, mock_session: AsyncMock) -> None:
        drafted = [make_report(title="Draft", status="draft")]
        count_mock = MagicMock()
        count_mock.scalar_one.return_value = 1
        fetch_mock = MagicMock()
        fetch_mock.scalars.return_value.all.return_value = drafted
        mock_session.execute.side_effect = [count_mock, fetch_mock]

        result, total = await report_service.list_reports(status="draft")
        assert total == 1
        call_stmt = mock_session.execute.call_args_list[0][0][0]
        compiled = str(call_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "draft" in compiled

    async def test_filters_by_author(self, report_service: ReportService, mock_session: AsyncMock) -> None:
        count_mock = MagicMock()
        count_mock.scalar_one.return_value = 0
        fetch_mock = MagicMock()
        fetch_mock.scalars.return_value.all.return_value = []
        mock_session.execute.side_effect = [count_mock, fetch_mock]

        await report_service.list_reports(author="Dr. Smith")
        call_stmt = mock_session.execute.call_args_list[0][0][0]
        compiled = str(call_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "Dr. Smith" in compiled

    async def test_filters_by_search(self, report_service: ReportService, mock_session: AsyncMock) -> None:
        count_mock = MagicMock()
        count_mock.scalar_one.return_value = 0
        fetch_mock = MagicMock()
        fetch_mock.scalars.return_value.all.return_value = []
        mock_session.execute.side_effect = [count_mock, fetch_mock]

        await report_service.list_reports(search="quarterly")
        call_stmt = mock_session.execute.call_args_list[0][0][0]
        compiled = str(call_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "%quarterly%" in compiled

    async def test_applies_all_filters_together(self, report_service: ReportService, mock_session: AsyncMock) -> None:
        count_mock = MagicMock()
        count_mock.scalar_one.return_value = 0
        fetch_mock = MagicMock()
        fetch_mock.scalars.return_value.all.return_value = []
        mock_session.execute.side_effect = [count_mock, fetch_mock]

        await report_service.list_reports(status="uploaded", author="Alice", search="Q4")
        # Verify that all three conditions were combined (AND)
        call_stmt = mock_session.execute.call_args_list[0][0][0]
        compiled = str(call_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "uploaded" in compiled
        assert "Alice" in compiled
        assert "%Q4%" in compiled


# ===================================================================
# Update
# ===================================================================


class TestUpdateReport:
    """``ReportService.update_report``"""

    async def test_updates_fields(self, report_service: ReportService) -> None:
        updated = make_report(title="New Title")
        await _patch_repos(report_service)
        report_service._report_repo.update.return_value = updated  # type: ignore[attr-defined]

        result = await report_service.update_report(updated.id, title="New Title")
        assert result is updated
        report_service._report_repo.update.assert_awaited_once_with(  # type: ignore[attr-defined]
            updated.id, title="New Title"
        )

    async def test_returns_none_when_not_found(self, report_service: ReportService) -> None:
        await _patch_repos(report_service)
        report_service._report_repo.update.return_value = None  # type: ignore[attr-defined]
        result = await report_service.update_report(uuid4(), title="Nope")
        assert result is None


# ===================================================================
# Delete
# ===================================================================


class TestDeleteReport:
    """``ReportService.delete_report``"""

    async def test_deletes_report_and_storage(
        self,
        report_service: ReportService,
        mock_storage: AsyncMock,
    ) -> None:
        """When the report exists, its versions' storage files are deleted too."""
        report_id = uuid4()
        v1_path = "reports/v1/doc.pdf"
        v2_path = "reports/v2/doc.pdf"
        report = make_report(
            id=report_id,
            versions=[
                make_version(report_id=report_id, version_number=1, storage_path=v1_path),
                make_version(report_id=report_id, version_number=2, storage_path=v2_path),
            ],
        )

        await _patch_repos(report_service)
        report_service._report_repo.get_with_versions.return_value = report  # type: ignore[attr-defined]
        report_service._report_repo.delete.return_value = True  # type: ignore[attr-defined]

        result = await report_service.delete_report(report_id)
        assert result is True

        # Storage delete called for each version
        mock_storage.delete.assert_has_awaits(
            [call(v1_path), call(v2_path)],
            any_order=True,
        )
        assert mock_storage.delete.await_count == 2

        # Report repo delete called
        report_service._report_repo.delete.assert_awaited_once_with(report_id)  # type: ignore[attr-defined]

    async def test_continues_on_storage_failure(
        self,
        report_service: ReportService,
        mock_storage: AsyncMock,
    ) -> None:
        """If storage.delete raises for one version, the report is still deleted."""
        report_id = uuid4()
        report = make_report(
            id=report_id,
            versions=[make_version(report_id=report_id, storage_path="some/path")],
        )

        await _patch_repos(report_service)
        report_service._report_repo.get_with_versions.return_value = report  # type: ignore[attr-defined]
        report_service._report_repo.delete.return_value = True  # type: ignore[attr-defined]
        mock_storage.delete.side_effect = Exception("Storage unavailable")

        result = await report_service.delete_report(report_id)
        assert result is True
        report_service._report_repo.delete.assert_awaited_once()  # type: ignore[attr-defined]

    async def test_returns_false_when_report_missing(self, report_service: ReportService) -> None:
        await _patch_repos(report_service)
        report_service._report_repo.get_with_versions.return_value = None  # type: ignore[attr-defined]
        result = await report_service.delete_report(uuid4())
        assert result is False
        report_service._report_repo.delete.assert_not_called()  # type: ignore[attr-defined]


# ===================================================================
# Versions
# ===================================================================


class TestUploadNewVersion:
    """``ReportService.upload_new_version``"""

    async def test_creates_version_two(
        self,
        report_service: ReportService,
        mock_storage: AsyncMock,
    ) -> None:
        """Uploading a new file for an existing report creates v2."""
        report_id = uuid4()
        existing = make_report(id=report_id)

        await _patch_repos(report_service)
        report_service._report_repo.get.return_value = existing  # type: ignore[attr-defined]
        report_service._version_repo.get_next_version_number.return_value = 2  # type: ignore[attr-defined]
        expected_version = make_version(report_id=report_id, version_number=2)
        report_service._version_repo.create.return_value = expected_version  # type: ignore[attr-defined]

        f = _mock_file(filename="v2.pdf", content=b"v2 content")
        result = await report_service.upload_new_version(report_id, file=f)

        assert result is expected_version
        assert result.version_number == 2

        # File stored
        mock_storage.store.assert_awaited_once()
        # Version created with correct number
        report_service._version_repo.create.assert_awaited_once()  # type: ignore[attr-defined]
        create_kwargs = report_service._version_repo.create.call_args[1]  # type: ignore[attr-defined]
        assert create_kwargs["version_number"] == 2
        assert create_kwargs["report_id"] == report_id

    async def test_raises_404_when_report_missing(self, report_service: ReportService) -> None:
        await _patch_repos(report_service)
        report_service._report_repo.get.return_value = None  # type: ignore[attr-defined]

        f = _mock_file()
        with pytest.raises(ProjectLensError) as exc_info:
            await report_service.upload_new_version(uuid4(), file=f)
        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "report_not_found"

    async def test_validates_file_before_upload(self, report_service: ReportService) -> None:
        report_id = uuid4()
        await _patch_repos(report_service)
        report_service._report_repo.get.return_value = make_report(id=report_id)  # type: ignore[attr-defined]

        f = _mock_file(filename="evil.exe")
        with pytest.raises(ProjectLensError) as exc_info:
            await report_service.upload_new_version(report_id, file=f)
        assert exc_info.value.code == "invalid_file_extension"
