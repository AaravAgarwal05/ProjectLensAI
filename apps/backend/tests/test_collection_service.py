"""Tests for :class:`CollectionService` — business logic layer.

The underlying repository is mocked so that only service-layer
orchestration and delegation are exercised.
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.database.models import Collection
from src.repository.collection import CollectionRepository
from src.services.collection_service import CollectionService

from .conftest import make_collection


class TestCreate:
    """``CollectionService.create``"""

    async def test_creates_collection(
        self,
        collection_service: CollectionService,
    ) -> None:
        expected = make_collection(name="Q2 Reports")
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.create.return_value = expected

        result = await collection_service.create(name="Q2 Reports", description="Second quarter collection")
        assert result is expected
        collection_service._repo.create.assert_awaited_once_with(
            name="Q2 Reports", description="Second quarter collection"
        )

    async def test_creates_without_description(
        self,
        collection_service: CollectionService,
    ) -> None:
        expected = make_collection(name="Minimal")
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.create.return_value = expected

        result = await collection_service.create(name="Minimal")
        assert result is expected
        collection_service._repo.create.assert_awaited_once_with(name="Minimal", description=None)


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

        result, total = await collection_service.list(skip=0, limit=10)
        assert list(result) == collections
        assert total == 3
        collection_service._repo.list.assert_awaited_once_with(skip=0, limit=10)

    async def test_empty_list(
        self,
        collection_service: CollectionService,
        mock_session: AsyncMock,
    ) -> None:
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.list.return_value = []
        mock_session.execute.return_value.scalar_one.return_value = 0

        result, total = await collection_service.list()
        assert result == []
        assert total == 0


class TestGet:
    """``CollectionService.get``"""

    async def test_returns_collection(
        self,
        collection_service: CollectionService,
    ) -> None:
        expected = make_collection()
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.get.return_value = expected

        result = await collection_service.get(expected.id)
        assert result is expected

    async def test_returns_none_when_missing(
        self,
        collection_service: CollectionService,
    ) -> None:
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.get.return_value = None

        result = await collection_service.get(uuid4())
        assert result is None


class TestUpdate:
    """``CollectionService.update``"""

    async def test_updates_fields(
        self,
        collection_service: CollectionService,
    ) -> None:
        updated = make_collection(name="New Name")
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.update.return_value = updated

        result = await collection_service.update(updated.id, name="New Name")
        assert result is updated
        collection_service._repo.update.assert_awaited_once_with(updated.id, name="New Name")

    async def test_returns_none_when_missing(
        self,
        collection_service: CollectionService,
    ) -> None:
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.update.return_value = None

        result = await collection_service.update(uuid4(), name="Nope")
        assert result is None


class TestDelete:
    """``CollectionService.delete``"""

    async def test_deletes_existing(
        self,
        collection_service: CollectionService,
    ) -> None:
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.delete.return_value = True

        result = await collection_service.delete(uuid4())
        assert result is True

    async def test_returns_false_when_missing(
        self,
        collection_service: CollectionService,
    ) -> None:
        collection_service._repo = AsyncMock(spec=CollectionRepository)
        collection_service._repo.delete.return_value = False

        result = await collection_service.delete(uuid4())
        assert result is False


class TestAddReport:
    """``CollectionService.add_report``"""

    async def test_adds_report(
        self,
        collection_service: CollectionService,
    ) -> None:
        col_id = uuid4()
        report_id = uuid4()
        collection_service._repo = AsyncMock(spec=CollectionRepository)

        await collection_service.add_report(col_id, report_id)
        collection_service._repo.add_report.assert_awaited_once_with(col_id, report_id)


class TestRemoveReport:
    """``CollectionService.remove_report``"""

    async def test_removes_report(
        self,
        collection_service: CollectionService,
    ) -> None:
        col_id = uuid4()
        report_id = uuid4()
        collection_service._repo = AsyncMock(spec=CollectionRepository)

        await collection_service.remove_report(col_id, report_id)
        collection_service._repo.remove_report.assert_awaited_once_with(col_id, report_id)
