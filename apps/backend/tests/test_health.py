"""Tests for the health-check endpoint.

The health endpoint checks database, ChromaDB, Ollama, and Redis
connectivity. In the test environment none of those are running,
so the endpoint returns ``down`` but still returns valid JSON.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_valid_response(client: AsyncClient) -> None:
    """GET /api/v1/health should return 200 with a valid status response."""
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    # Accept any valid status — deps aren't running in test env
    assert body["status"] in ("ok", "degraded", "down")
    assert "version" in body
    assert "timestamp" in body
    assert "checks" in body
    checks = body["checks"]
    for dep in ("database", "chromadb", "ollama", "redis"):
        assert dep in checks
        assert "status" in checks[dep]
        assert "latency_ms" in checks[dep]
