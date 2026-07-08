"""Tests for :class:`ReportRepository` — all DB access is mocked.

Every test uses a mocked ``AsyncSession`` whose ``execute`` / ``get``
return values are wired per scenario so we can verify the repository
methods construct the correct queries and return the expected data.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from src.database.models import Report
from src.repository.report import ReportRepository


@pytest.fixture
def repo(mock_session: AsyncMock) -> ReportRepository:
    """Return a ``ReportRepository`` bound to the mocked session."""
    return ReportRepository(session=mock_session)


class TestCreateReport:
    """``ReportRepository.create``"""

    async def test_creates_and_returns_report(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        report = await repo.create(
            title="New Report",
            description="A description",
            status="draft",
            storage_provider="supabase",
        )
        assert report.title == "New Report"
        assert report.description == "A description"
        assert report.status == "draft"
        assert report.storage_provider == "supabase"
        mock_session.add.assert_called_once()
        assert mock_session.flush.await_count == 1

    async def test_includes_all_kwargs(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        author = "Dr. Smith"
        report = await repo.create(
            title="Research Q1",
            author=author,
            department="R&D",
            tags=["ml", "research"],
            visibility="internal",
            year=2025,
        )
        assert report.author == author
        assert report.department == "R&D"
        assert report.tags == ["ml", "research"]
        assert report.visibility == "internal"
        assert report.year == 2025


class TestGetReport:
    """``ReportRepository.get``"""

    async def test_returns_report_when_found(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        report_id = uuid4()
        expected = Report(id=report_id, title="Existing Report")
        mock_session.get.return_value = expected

        result = await repo.get(report_id)
        assert result is expected
        mock_session.get.assert_awaited_once_with(Report, report_id)

    async def test_returns_none_when_missing(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        mock_session.get.return_value = None
        result = await repo.get(uuid4())
        assert result is None


class TestListReports:
    """``ReportRepository.list`` with skip/limit"""

    async def test_pagination(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        reports = [Report(title=f"Report {i}") for i in range(3)]
        mock_session.execute.return_value.scalars.return_value.all.return_value = reports

        result = await repo.list(skip=10, limit=5)
        assert len(result) == 3
        # The internal select statement includes .offset(10).limit(5)
        call_stmt = mock_session.execute.call_args[0][0]
        assert call_stmt._limit == 5
        assert call_stmt._offset == 10

    async def test_filters_by_field(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        reports = [Report(title="Public Report")]
        mock_session.execute.return_value.scalars.return_value.all.return_value = reports

        result = await repo.list(visibility="public")
        assert len(result) == 1
        call_stmt = mock_session.execute.call_args[0][0]
        compiled = str(call_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "visibility" in compiled


class TestGetByStatus:
    """``ReportRepository.get_by_status``"""

    async def test_filters_by_status(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        expected = [Report(title="Uploaded 1", status="uploaded")]
        mock_session.execute.return_value.scalars.return_value.all.return_value = expected

        result = await repo.get_by_status("uploaded")
        assert result == expected
        call_stmt = mock_session.execute.call_args[0][0]
        compiled = str(call_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "uploaded" in compiled

    async def test_respects_skip_limit(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        await repo.get_by_status("draft", skip=5, limit=10)
        call_stmt = mock_session.execute.call_args[0][0]
        assert call_stmt._limit == 10
        assert call_stmt._offset == 5

    async def test_returns_empty_when_no_match(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        result = await repo.get_by_status("nonexistent")
        assert result == []


class TestSearch:
    """``ReportRepository.search`` — ILIKE on title & description"""

    async def test_matches_title(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        matched = [Report(title="Annual Report 2024")]
        mock_session.execute.return_value.scalars.return_value.all.return_value = matched

        result = await repo.search("annual")
        assert result == matched

    async def test_matches_description(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        matched = [Report(title="Doc", description="This is the quarterly review")]
        mock_session.execute.return_value.scalars.return_value.all.return_value = matched

        result = await repo.search("quarterly")
        assert result == matched
        call_stmt = mock_session.execute.call_args[0][0]
        compiled = str(call_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "%quarterly%" in compiled

    async def test_returns_empty_on_no_match(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        result = await repo.search("zzzznotfound")
        assert result == []


class TestDeleteReport:
    """``ReportRepository.delete``"""

    async def test_deletes_existing_report(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        report_id = uuid4()
        mock_session.get.return_value = Report(id=report_id, title="To Delete")
        result = await repo.delete(report_id)
        assert result is True
        mock_session.delete.assert_awaited_once()

    async def test_returns_false_when_missing(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        mock_session.get.return_value = None
        result = await repo.delete(uuid4())
        assert result is False


class TestGetWithVersions:
    """``ReportRepository.get_with_versions`` — eager-loads versions"""

    async def test_returns_report_with_versions(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        report_id = uuid4()
        expected = Report(id=report_id, title="With Versions")
        result_mock = MagicMock()
        result_mock.unique.return_value.scalar_one_or_none.return_value = expected
        mock_session.execute.return_value = result_mock

        result = await repo.get_with_versions(report_id)
        assert result is expected
        # Verify joinedload was applied (SELECT FROM reports LEFT OUTER JOIN report_versions)
        call_stmt = mock_session.execute.call_args[0][0]
        compiled = str(call_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "report_versions" in compiled

    async def test_returns_none_when_missing(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        result_mock = MagicMock()
        result_mock.unique.return_value.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = result_mock
        result = await repo.get_with_versions(uuid4())
        assert result is None


class TestCountByStatus:
    """``ReportRepository.count_by_status``"""

    async def test_counts_matching_reports(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        mock_session.execute.return_value.scalar_one.return_value = 7
        count = await repo.count_by_status("uploaded")
        assert count == 7

    async def test_returns_zero_when_none(self, repo: ReportRepository, mock_session: AsyncMock) -> None:
        mock_session.execute.return_value.scalar_one.return_value = 0
        count = await repo.count_by_status("archived")
        assert count == 0
