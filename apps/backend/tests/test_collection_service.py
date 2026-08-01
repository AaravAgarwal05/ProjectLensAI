"""Tests for :class:`CollectionService` — business logic layer.

The underlying repository is mocked so that only service-layer
orchestration, ownership enforcement, and delegation are exercised.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.api.exceptions import ProjectLensError
from src.database.models import Collection
from src.repository.collection import CollectionRepository
from src.services.collection_service import CollectionService

from .conftest import make_collection, make_report


class TestCreate:
    """``CollectionService.create``"""

    async def test_creates_collection(
        self,
        collection_service: CollectionService,
    ) -> None:
        expected = make_collection(name="Q2 Reports")
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.create.return_value = expected

        result = await collection_service.create(
            name="Q2 Reports", owner_id="owner-1", description="Second quarter collection"
        )
        assert result is expected
        collection_service._repo.create.assert_awaited_once_with(
            name="Q2 Reports", owner_id="owner-1", description="Second quarter collection"
        )

    async def test_creates_without_description(
        self,
        collection_service: CollectionService,
    ) -> None:
        expected = make_collection(name="Minimal")
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.create.return_value = expected

        result = await collection_service.create(name="Minimal", owner_id="owner-1")
        assert result is expected
        collection_service._repo.create.assert_awaited_once_with(
            name="Minimal", owner_id="owner-1", description=None
        )


class TestList:
    """``CollectionService.list``"""

    async def test_returns_paginated_results(
        self,
        collection_service: CollectionService,
        mock_session: AsyncMock,
    ) -> None:
        collections = [make_collection(name=f"C{i}") for i in range(3)]
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.list.return_value = collections

        # list() also does a count query via self._session
        mock_session.execute.return_value.scalar_one.return_value = 3

        result, total = await collection_service.list(owner_id="owner-1", skip=0, limit=10)
        assert list(result) == collections
        assert total == 3
        collection_service._repo.list.assert_awaited_once_with(
            owner_id="owner-1", skip=0, limit=10
        )

    async def test_empty_list(
        self,
        collection_service: CollectionService,
        mock_session: AsyncMock,
    ) -> None:
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.list.return_value = []
        mock_session.execute.return_value.scalar_one.return_value = 0

        result, total = await collection_service.list(owner_id="owner-1")
        assert result == []
        assert total == 0


class TestGet:
    """``CollectionService.get``"""

    async def test_returns_collection(
        self,
        collection_service: CollectionService,
    ) -> None:
        expected = make_collection(owner_id="owner-1")
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.get.return_value = expected

        result = await collection_service.get(expected.id, owner_id="owner-1")
        assert result is expected

    async def test_raises_404_when_missing(
        self,
        collection_service: CollectionService,
    ) -> None:
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.get.return_value = None

        with pytest.raises(ProjectLensError) as exc_info:
            await collection_service.get(uuid4(), owner_id="owner-1")
        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "collection_not_found"

    async def test_raises_404_for_foreign_owner(
        self,
        collection_service: CollectionService,
    ) -> None:
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.get.return_value = make_collection(owner_id="someone-else")

        with pytest.raises(ProjectLensError) as exc_info:
            await collection_service.get(uuid4(), owner_id="owner-1")
        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "collection_not_found"


class TestUpdate:
    """``CollectionService.update``"""

    async def test_updates_fields(
        self,
        collection_service: CollectionService,
    ) -> None:
        updated = make_collection(owner_id="owner-1", name="New Name")
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.get.return_value = updated
        collection_service._repo.update.return_value = updated

        result = await collection_service.update(updated.id, owner_id="owner-1", name="New Name")
        assert result is updated
        collection_service._repo.update.assert_awaited_once_with(updated.id, name="New Name")

    async def test_raises_404_when_missing(
        self,
        collection_service: CollectionService,
    ) -> None:
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.get.return_value = None

        with pytest.raises(ProjectLensError) as exc_info:
            await collection_service.update(uuid4(), owner_id="owner-1", name="Nope")
        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "collection_not_found"


class TestDelete:
    """``CollectionService.delete``"""

    async def test_deletes_existing(
        self,
        collection_service: CollectionService,
    ) -> None:
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.get.return_value = make_collection(owner_id="owner-1")
        collection_service._repo.delete.return_value = True

        result = await collection_service.delete(uuid4(), owner_id="owner-1")
        assert result is True

    async def test_raises_404_when_missing(
        self,
        collection_service: CollectionService,
    ) -> None:
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.get.return_value = None
        collection_service._repo.delete.return_value = False

        with pytest.raises(ProjectLensError) as exc_info:
            await collection_service.delete(uuid4(), owner_id="owner-1")
        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "collection_not_found"


class TestAddReport:
    """``CollectionService.add_report`` — both collection and report must be owned."""

    async def test_adds_report(
        self,
        collection_service: CollectionService,
        mock_session: AsyncMock,
    ) -> None:
        col_id = uuid4()
        report_id = uuid4()
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.get.return_value = make_collection(owner_id="owner-1")
        mock_session.get.return_value = make_report(owner_id="owner-1")

        await collection_service.add_report(col_id, report_id, owner_id="owner-1")
        collection_service._repo.add_report.assert_awaited_once_with(col_id, report_id)

    async def test_raises_404_when_report_foreign(
        self,
        collection_service: CollectionService,
        mock_session: AsyncMock,
    ) -> None:
        col_id = uuid4()
        report_id = uuid4()
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.get.return_value = make_collection(owner_id="owner-1")
        mock_session.get.return_value = make_report(owner_id="someone-else")

        with pytest.raises(ProjectLensError) as exc_info:
            await collection_service.add_report(col_id, report_id, owner_id="owner-1")
        assert exc_info.value.status_code == 404
        collection_service._repo.add_report.assert_not_called()


class TestRemoveReport:
    """``CollectionService.remove_report``"""

    async def test_removes_report(
        self,
        collection_service: CollectionService,
    ) -> None:
        col_id = uuid4()
        report_id = uuid4()
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.get.return_value = make_collection(owner_id="owner-1")

        await collection_service.remove_report(col_id, report_id, owner_id="owner-1")
        collection_service._repo.remove_report.assert_awaited_once_with(col_id, report_id)
