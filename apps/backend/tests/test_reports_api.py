"""Integration tests for the ``/api/v1/reports`` HTTP endpoints.

Every test uses the ``api_client`` fixture which overrides FastAPI
dependencies (DB, auth, settings) with mocks.  Service-layer methods
are patched at the class level so that no real storage or database
operations execute.
"""

from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from src.api.exceptions import ProjectLensError
from src.services import ReportService

from .conftest import make_report, make_version


class TestUploadReport:
    """POST /api/v1/reports"""

    async def test_returns_201_with_report_data(self, api_client: AsyncClient) -> None:
        report_id = uuid4()
        expected = make_report(id=report_id, title="Annual Report", tags=["finance"])
        with patch.object(ReportService, "create_report", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = expected

            response = await api_client.post(
                "/api/v1/reports",
                data={"title": "Annual Report", "description": "Full year", "tags": "finance,report"},
                files={"file": ("report.pdf", b"pdf content here", "application/pdf")},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(report_id)
        assert data["title"] == "Annual Report"
        assert data["status"] == "uploaded"
        assert data["tags"] == ["finance"]
        assert "created_at" in data
        assert "updated_at" in data

    async def test_returns_201_without_optional_fields(self, api_client: AsyncClient) -> None:
        expected = make_report(description=None, author=None, tags=None)
        with patch.object(ReportService, "create_report", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = expected

            response = await api_client.post(
                "/api/v1/reports",
                data={"title": "Minimal"},
                files={"file": ("doc.txt", b"text", "text/plain")},
            )

        assert response.status_code == 201

    async def test_invalid_file_type_returns_400(self, api_client: AsyncClient) -> None:
        with patch.object(ReportService, "create_report", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = ProjectLensError(
                message="File extension '.exe' is not allowed. Allowed: .pdf, .docx, .txt",
                code="invalid_file_extension",
                status_code=400,
            )

            response = await api_client.post(
                "/api/v1/reports",
                data={"title": "Bad"},
                files={"file": ("virus.exe", b"boom", "application/octet-stream")},
            )

        assert response.status_code == 400
        error = response.json()["error"]
        assert error["code"] == "invalid_file_extension"

    async def test_file_too_large_returns_413(self, api_client: AsyncClient) -> None:
        with patch.object(ReportService, "create_report", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = ProjectLensError(
                message="File exceeds the maximum upload size of 1 MiB.",
                code="file_too_large",
                status_code=413,
            )

            response = await api_client.post(
                "/api/v1/reports",
                data={"title": "Huge"},
                files={"file": ("big.pdf", b"x" * 2000000, "application/pdf")},
            )

        assert response.status_code == 413
        assert response.json()["error"]["code"] == "file_too_large"


class TestListReports:
    """GET /api/v1/reports"""

    async def test_returns_paginated_list(self, api_client: AsyncClient) -> None:
        reports = [make_report(title=f"Report {i}") for i in range(2)]
        with patch.object(ReportService, "list_reports", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = (reports, 10)

            response = await api_client.get("/api/v1/reports?skip=0&limit=10")

        assert response.status_code == 200
        body = response.json()
        assert len(body["items"]) == 2
        assert body["total"] == 10
        assert body["skip"] == 0
        assert body["limit"] == 10

    async def test_passes_query_filters(self, api_client: AsyncClient) -> None:
        with patch.object(ReportService, "list_reports", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = ([], 0)

            await api_client.get("/api/v1/reports?status=draft&author=Alice&search=Q4")

        mock_list.assert_awaited_once()
        kwargs = mock_list.call_args[1]
        assert kwargs["status"] == "draft"
        assert kwargs["author"] == "Alice"
        assert kwargs["search"] == "Q4"

    async def test_enforces_limit_cap(self, api_client: AsyncClient) -> None:
        """FastAPI rejects ``limit`` values above the declared maximum."""
        response = await api_client.get("/api/v1/reports?limit=999")
        assert response.status_code == 422


class TestGetReport:
    """GET /api/v1/reports/{report_id}"""

    async def test_returns_report(self, api_client: AsyncClient) -> None:
        report_id = uuid4()
        expected = make_report(id=report_id, title="Specific Report")
        with patch.object(ReportService, "get_report", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = expected

            response = await api_client.get(f"/api/v1/reports/{report_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(report_id)
        assert data["title"] == "Specific Report"

    async def test_404_when_not_found(self, api_client: AsyncClient) -> None:
        with patch.object(ReportService, "get_report", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            response = await api_client.get(f"/api/v1/reports/{uuid4()}")

        assert response.status_code == 404
        assert "not found" in response.json()["error"]["message"]


class TestUpdateReport:
    """PATCH /api/v1/reports/{report_id}"""

    async def test_updates_and_returns_report(self, api_client: AsyncClient) -> None:
        report_id = uuid4()
        updated = make_report(id=report_id, title="Updated Title", status="published")
        with patch.object(ReportService, "update_report", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = updated

            response = await api_client.patch(
                f"/api/v1/reports/{report_id}",
                json={"title": "Updated Title", "status": "published"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "published"

    async def test_400_when_no_fields(self, api_client: AsyncClient) -> None:
        response = await api_client.patch(
            f"/api/v1/reports/{uuid4()}",
            json={},
        )
        assert response.status_code == 400

    async def test_404_when_report_missing(self, api_client: AsyncClient) -> None:
        with patch.object(ReportService, "update_report", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = None

            response = await api_client.patch(
                f"/api/v1/reports/{uuid4()}",
                json={"title": "Nope"},
            )

        assert response.status_code == 404


class TestDeleteReport:
    """DELETE /api/v1/reports/{report_id}"""

    async def test_returns_204_and_then_404(self, api_client: AsyncClient) -> None:
        report_id = uuid4()
        with patch.object(ReportService, "delete_report", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            response = await api_client.delete(f"/api/v1/reports/{report_id}")
            assert response.status_code == 204

        # Subsequent GET returns 404
        with patch.object(ReportService, "get_report", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            response = await api_client.get(f"/api/v1/reports/{report_id}")
            assert response.status_code == 404

    async def test_404_when_report_missing(self, api_client: AsyncClient) -> None:
        with patch.object(ReportService, "delete_report", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = False
            response = await api_client.delete(f"/api/v1/reports/{uuid4()}")
            assert response.status_code == 404


class TestUploadVersion:
    """POST /api/v1/reports/{report_id}/versions"""

    async def test_creates_version_two(self, api_client: AsyncClient) -> None:
        report_id = uuid4()
        v2 = make_version(report_id=report_id, version_number=2, original_filename="v2.pdf")
        with patch.object(ReportService, "upload_new_version", new_callable=AsyncMock) as mock_upload:
            mock_upload.return_value = v2

            response = await api_client.post(
                f"/api/v1/reports/{report_id}/versions",
                files={"file": ("v2.pdf", b"newer content", "application/pdf")},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["version_number"] == 2
        assert data["original_filename"] == "v2.pdf"

    async def test_404_when_report_missing(self, api_client: AsyncClient) -> None:
        with patch.object(ReportService, "upload_new_version", new_callable=AsyncMock) as mock_upload:
            mock_upload.side_effect = ProjectLensError(
                message="Report not found",
                code="report_not_found",
                status_code=404,
            )

            response = await api_client.post(
                f"/api/v1/reports/{uuid4()}/versions",
                files={"file": ("v1.pdf", b"x", "application/pdf")},
            )

        assert response.status_code == 404


class TestListVersions:
    """GET /api/v1/reports/{report_id}/versions"""

    async def test_returns_version_list(self, api_client: AsyncClient) -> None:
        report_id = uuid4()
        versions = [
            make_version(report_id=report_id, version_number=1, original_filename="v1.pdf"),
            make_version(report_id=report_id, version_number=2, original_filename="v2.pdf"),
        ]
        report = make_report(id=report_id, versions=versions)
        with patch.object(ReportService, "get_report", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = report

            response = await api_client.get(f"/api/v1/reports/{report_id}/versions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["version_number"] == 1
        assert data[1]["version_number"] == 2

    async def test_404_when_report_missing(self, api_client: AsyncClient) -> None:
        with patch.object(ReportService, "get_report", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            response = await api_client.get(f"/api/v1/reports/{uuid4()}/versions")
            assert response.status_code == 404


class TestNonexistentReport:
    """All GET/PATCH/DELETE routes return 404 for missing reports."""

    async def test_get_nonexistent(self, api_client: AsyncClient) -> None:
        with patch.object(ReportService, "get_report", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            response = await api_client.get(f"/api/v1/reports/{uuid4()}")
            assert response.status_code == 404

    async def test_patch_nonexistent(self, api_client: AsyncClient) -> None:
        with patch.object(ReportService, "update_report", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = None
            response = await api_client.patch(
                f"/api/v1/reports/{uuid4()}", json={"title": "Nope"}
            )
            assert response.status_code == 404

    async def test_delete_nonexistent(self, api_client: AsyncClient) -> None:
        with patch.object(ReportService, "delete_report", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = False
            response = await api_client.delete(f"/api/v1/reports/{uuid4()}")
            assert response.status_code == 404
