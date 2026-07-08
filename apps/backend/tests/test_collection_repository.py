"""Tests for :class:`CollectionRepository` — all DB access is mocked.

Covers CRUD, name-based lookups, and many-to-many association
management between collections and reports.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.database.models import Collection, CollectionReport, Report
from src.repository.collection import CollectionRepository


@pytest.fixture
def repo(mock_session: AsyncMock) -> CollectionRepository:
    """Return a ``CollectionRepository`` bound to the mocked session."""
    return CollectionRepository(session=mock_session)


class TestCreateCollection:
    """``CollectionRepository.create``"""

    async def test_creates_with_name(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        collection = await repo.create(name="Q1 Reports", description="First quarter")
        assert collection.name == "Q1 Reports"
        assert collection.description == "First quarter"
        mock_session.add.assert_called_once()
        assert mock_session.flush.await_count == 1

    async def test_defaults_description_to_none(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        collection = await repo.create(name="Minimal")
        assert collection.name == "Minimal"
        assert collection.description is None


class TestGetCollection:
    """``CollectionRepository.get``"""

    async def test_returns_collection_when_found(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        col_id = uuid4()
        expected = Collection(id=col_id, name="Reports")
        mock_session.get.return_value = expected
        result = await repo.get(col_id)
        assert result is expected

    async def test_returns_none_when_missing(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        mock_session.get.return_value = None
        result = await repo.get(uuid4())
        assert result is None


class TestGetByName:
    """``CollectionRepository.get_by_name``"""

    async def test_finds_by_exact_name(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        expected = Collection(name="Engineering Reports")
        mock_session.execute.return_value.scalar_one_or_none.return_value = expected
        result = await repo.get_by_name("Engineering Reports")
        assert result is expected

    async def test_returns_none_when_not_found(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        result = await repo.get_by_name("Nonexistent")
        assert result is None


class TestListCollections:
    """``CollectionRepository.list``"""

    async def test_respects_pagination(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        collections = [Collection(name=f"C{i}") for i in range(2)]
        mock_session.execute.return_value.scalars.return_value.all.return_value = collections
        result = await repo.list(skip=0, limit=10)
        assert len(result) == 2


class TestUpdateCollection:
    """``CollectionRepository.update``"""

    async def test_updates_fields(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        col_id = uuid4()
        existing = Collection(id=col_id, name="Old Name", description="Old desc")
        mock_session.get.return_value = existing

        updated = await repo.update(col_id, name="New Name")
        assert updated is not None
        assert updated.name == "New Name"
        mock_session.flush.assert_awaited_once()

    async def test_returns_none_when_missing(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        mock_session.get.return_value = None
        result = await repo.update(uuid4(), name="Nope")
        assert result is None


class TestDeleteCollection:
    """``CollectionRepository.delete``"""

    async def test_deletes_existing(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        col_id = uuid4()
        mock_session.get.return_value = Collection(id=col_id, name="To Delete")
        result = await repo.delete(col_id)
        assert result is True
        mock_session.delete.assert_awaited_once()

    async def test_returns_false_when_missing(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        mock_session.get.return_value = None
        result = await repo.delete(uuid4())
        assert result is False


class TestAddReport:
    """``CollectionRepository.add_report``"""

    async def test_adds_association_when_new(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        """Should create a ``CollectionReport`` row when none exists."""
        col_id = uuid4()
        report_id = uuid4()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        await repo.add_report(col_id, report_id)

        # Verify the association was added
        added: CollectionReport = mock_session.add.call_args[0][0]
        assert added.collection_id == col_id
        assert added.report_id == report_id
        assert mock_session.flush.await_count == 1

    async def test_skips_when_already_linked(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        """Should be a no-op when the association already exists."""
        col_id = uuid4()
        report_id = uuid4()
        existing = CollectionReport(collection_id=col_id, report_id=report_id)
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing

        await repo.add_report(col_id, report_id)

        # add should NOT have been called
        mock_session.add.assert_not_called()
        # flush should NOT have been called
        assert mock_session.flush.await_count == 0


class TestRemoveReport:
    """``CollectionRepository.remove_report``"""

    async def test_removes_association_when_linked(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        col_id = uuid4()
        report_id = uuid4()
        existing = CollectionReport(collection_id=col_id, report_id=report_id)
        mock_session.execute.return_value.scalar_one_or_none.return_value = existing

        await repo.remove_report(col_id, report_id)

        mock_session.delete.assert_awaited_once_with(existing)
        assert mock_session.flush.await_count == 1

    async def test_skips_when_not_linked(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        col_id = uuid4()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        await repo.remove_report(col_id, uuid4())

        mock_session.delete.assert_not_called()


class TestGetReportsForCollection:
    """``CollectionRepository.get_reports_for_collection``"""

    async def test_returns_associated_reports(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        col_id = uuid4()
        reports = [Report(title="R1"), Report(title="R2")]
        mock_session.execute.return_value.scalars.return_value.all.return_value = reports

        result = await repo.get_reports_for_collection(col_id)
        assert result == reports
        call_stmt = mock_session.execute.call_args[0][0]
        compiled = str(call_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "collection_reports" in compiled

    async def test_returns_empty_for_empty_collection(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        result = await repo.get_reports_for_collection(uuid4())
        assert result == []

    async def test_respects_pagination(self, repo: CollectionRepository, mock_session: AsyncMock) -> None:
        await repo.get_reports_for_collection(uuid4(), skip=5, limit=25)
        call_stmt = mock_session.execute.call_args[0][0]
        assert call_stmt._limit == 25
        assert call_stmt._offset == 5
