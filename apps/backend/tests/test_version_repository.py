"""Tests for :class:`VersionRepository` — all DB access is mocked.

Covers creation, retrieval ordering, latest-version lookups, and
auto-incrementing version numbers for the ``ReportVersion`` model.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.database.models import ReportVersion
from src.repository.version import VersionRepository


@pytest.fixture
def repo(mock_session: AsyncMock) -> VersionRepository:
    """Return a ``VersionRepository`` bound to the mocked session."""
    return VersionRepository(session=mock_session)


class TestCreateVersion:
    """``VersionRepository.create``"""

    async def test_creates_with_required_fields(self, repo: VersionRepository, mock_session: AsyncMock) -> None:
        report_id = uuid4()
        version = await repo.create(
            report_id=report_id,
            version_number=1,
            storage_path="reports/a/b.pdf",
            original_filename="b.pdf",
            mime_type="application/pdf",
            checksum="deadbeef",
            file_size=999,
        )
        assert version.report_id == report_id
        assert version.version_number == 1
        assert version.storage_path == "reports/a/b.pdf"
        assert version.original_filename == "b.pdf"
        assert version.mime_type == "application/pdf"
        assert version.file_size == 999
        mock_session.add.assert_called_once()
        assert mock_session.flush.await_count == 1


class TestGetVersionsForReport:
    """``VersionRepository.get_versions_for_report`` — ordered by version_number ASC"""

    async def test_returns_all_versions_ordered(self, repo: VersionRepository, mock_session: AsyncMock) -> None:
        report_id = uuid4()
        v1 = ReportVersion(report_id=report_id, version_number=1)
        v2 = ReportVersion(report_id=report_id, version_number=2)
        mock_session.execute.return_value.scalars.return_value.all.return_value = [v1, v2]

        versions = await repo.get_versions_for_report(report_id)
        assert versions == [v1, v2]

        call_stmt = mock_session.execute.call_args[0][0]
        compiled = str(call_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "report_versions" in compiled
        # compiled SQL uses PostgreSQL-native UUID format (no dashes)
        assert report_id.hex in compiled

    async def test_returns_empty_when_no_versions(self, repo: VersionRepository, mock_session: AsyncMock) -> None:
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        versions = await repo.get_versions_for_report(uuid4())
        assert versions == []


class TestGetLatestVersion:
    """``VersionRepository.get_latest_version`` — highest version_number"""

    async def test_returns_highest_version(self, repo: VersionRepository, mock_session: AsyncMock) -> None:
        report_id = uuid4()
        v3 = ReportVersion(report_id=report_id, version_number=3)
        mock_session.execute.return_value.scalar_one_or_none.return_value = v3

        result = await repo.get_latest_version(report_id)
        assert result is v3

        call_stmt = mock_session.execute.call_args[0][0]
        compiled = str(call_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "DESC" in compiled.upper() or "DESC" in str(call_stmt)

    async def test_returns_none_when_no_versions(self, repo: VersionRepository, mock_session: AsyncMock) -> None:
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        result = await repo.get_latest_version(uuid4())
        assert result is None


class TestGetNextVersionNumber:
    """``VersionRepository.get_next_version_number``"""

    async def test_starts_at_one_when_no_versions(self, repo: VersionRepository, mock_session: AsyncMock) -> None:
        mock_session.execute.return_value.scalar_one.return_value = None
        next_num = await repo.get_next_version_number(uuid4())
        assert next_num == 1

    async def test_increments_from_existing_max(self, repo: VersionRepository, mock_session: AsyncMock) -> None:
        mock_session.execute.return_value.scalar_one.return_value = 5
        next_num = await repo.get_next_version_number(uuid4())
        assert next_num == 6

    async def test_handles_large_version_numbers(self, repo: VersionRepository, mock_session: AsyncMock) -> None:
        mock_session.execute.return_value.scalar_one.return_value = 99
        next_num = await repo.get_next_version_number(uuid4())
        assert next_num == 100
