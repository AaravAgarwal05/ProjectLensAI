"""Integration tests for the ``/api/v1/collections`` HTTP endpoints.

Uses the same ``api_client`` fixture with dependency overrides as the
reports API tests.  Service-layer methods are patched at the class
level so that no real database operations execute.
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.services import CollectionService

from .conftest import make_collection


class TestCreateCollection:
    """POST /api/v1/collections"""

    async def test_returns_201_with_data(self, api_client: AsyncClient) -> None:
        col_id = uuid4()
        expected = make_collection(id=col_id, name="Q1 Reports", description="First quarter collection")
        with patch.object(CollectionService, "create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = expected

            response = await api_client.post(
                "/api/v1/collections",
                json={"name": "Q1 Reports", "description": "First quarter collection"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(col_id)
        assert data["name"] == "Q1 Reports"
        assert data["description"] == "First quarter collection"

    async def test_requires_name(self, api_client: AsyncClient) -> None:
        response = await api_client.post("/api/v1/collections", json={})
        assert response.status_code == 422

    async def test_accepts_without_description(self, api_client: AsyncClient) -> None:
        expected = make_collection(name="Minimal")
        with patch.object(CollectionService, "create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = expected

            response = await api_client.post(
                "/api/v1/collections",
                json={"name": "Minimal"},
            )

        assert response.status_code == 201
        assert response.json()["name"] == "Minimal"


class TestListCollections:
    """GET /api/v1/collections"""

    async def test_returns_paginated_list(self, api_client: AsyncClient) -> None:
        collections = [make_collection(name=f"C{i}") for i in range(3)]
        with patch.object(CollectionService, "list", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = (collections, 10)

            response = await api_client.get("/api/v1/collections?skip=0&limit=10")

        assert response.status_code == 200
        body = response.json()
        assert len(body["items"]) == 3
        assert body["total"] == 10
        assert body["skip"] == 0
        assert body["limit"] == 10

    async def test_defaults_pagination(self, api_client: AsyncClient) -> None:
        with patch.object(CollectionService, "list", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = ([], 0)

            await api_client.get("/api/v1/collections")

        kwargs = mock_list.call_args[1]
        assert kwargs["skip"] == 0
        assert kwargs["limit"] == 20

    async def test_enforces_limit_cap(self, api_client: AsyncClient) -> None:
        """FastAPI rejects ``limit`` values above the declared maximum."""
        response = await api_client.get("/api/v1/collections?limit=999")
        assert response.status_code == 422


class TestGetCollection:
    """GET /api/v1/collections/{collection_id}"""

    async def test_returns_collection(self, api_client: AsyncClient) -> None:
        col_id = uuid4()
        expected = make_collection(id=col_id, name="My Collection")
        with patch.object(CollectionService, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = expected

            response = await api_client.get(f"/api/v1/collections/{col_id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(col_id)

    async def test_404_when_not_found(self, api_client: AsyncClient) -> None:
        with patch.object(CollectionService, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            response = await api_client.get(f"/api/v1/collections/{uuid4()}")
        assert response.status_code == 404


class TestUpdateCollection:
    """PATCH /api/v1/collections/{collection_id}"""

    async def test_updates_and_returns(self, api_client: AsyncClient) -> None:
        col_id = uuid4()
        updated = make_collection(id=col_id, name="New Name")
        with patch.object(CollectionService, "update", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = updated

            response = await api_client.patch(
                f"/api/v1/collections/{col_id}",
                json={"name": "New Name"},
            )

        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    async def test_400_when_no_fields(self, api_client: AsyncClient) -> None:
        response = await api_client.patch(
            f"/api/v1/collections/{uuid4()}",
            json={},
        )
        assert response.status_code == 400

    async def test_404_when_missing(self, api_client: AsyncClient) -> None:
        with patch.object(CollectionService, "update", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = None

            response = await api_client.patch(
                f"/api/v1/collections/{uuid4()}",
                json={"name": "Nope"},
            )
        assert response.status_code == 404


class TestDeleteCollection:
    """DELETE /api/v1/collections/{collection_id}"""

    async def test_returns_204(self, api_client: AsyncClient) -> None:
        with patch.object(CollectionService, "delete", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True

            response = await api_client.delete(f"/api/v1/collections/{uuid4()}")
        assert response.status_code == 204

    async def test_404_when_missing(self, api_client: AsyncClient) -> None:
        with patch.object(CollectionService, "delete", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = False

            response = await api_client.delete(f"/api/v1/collections/{uuid4()}")
        assert response.status_code == 404


class TestAddReportToCollection:
    """POST /api/v1/collections/{collection_id}/reports/{report_id}"""

    async def test_returns_200(self, api_client: AsyncClient) -> None:
        col_id = uuid4()
        report_id = uuid4()
        with (
            patch.object(CollectionService, "get", new_callable=AsyncMock) as mock_get,
            patch.object(CollectionService, "add_report", new_callable=AsyncMock) as mock_add,
        ):
            mock_get.return_value = make_collection(id=col_id)

            response = await api_client.post(f"/api/v1/collections/{col_id}/reports/{report_id}")

        assert response.status_code == 200
        assert response.json() == {"message": "Report added to collection"}
        mock_add.assert_awaited_once_with(col_id, report_id)

    async def test_404_when_collection_missing(self, api_client: AsyncClient) -> None:
        with patch.object(CollectionService, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            response = await api_client.post(
                f"/api/v1/collections/{uuid4()}/reports/{uuid4()}"
            )
        assert response.status_code == 404


class TestRemoveReportFromCollection:
    """DELETE /api/v1/collections/{collection_id}/reports/{report_id}"""

    async def test_returns_204(self, api_client: AsyncClient) -> None:
        col_id = uuid4()
        report_id = uuid4()
        with patch.object(CollectionService, "remove_report", new_callable=AsyncMock) as mock_remove:
            response = await api_client.delete(f"/api/v1/collections/{col_id}/reports/{report_id}")

        assert response.status_code == 204
        mock_remove.assert_awaited_once_with(col_id, report_id)
