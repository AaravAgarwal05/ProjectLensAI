"""Tests for the security headers and cross-site (CSRF) guard middleware."""

import httpx
import pytest
from fastapi import FastAPI

from src.api.middleware import add_middleware


def _make_app() -> FastAPI:
    """A minimal app with the real middleware stack and two dummy routes."""
    app = FastAPI()
    add_middleware(app)

    @app.get("/ping")
    async def ping() -> dict:
        return {"ok": True}

    @app.post("/echo")
    async def echo() -> dict:
        return {"ok": True}

    return app


@pytest.fixture
def app_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=_make_app()),
        base_url="http://test",
    )


async def test_security_headers_present(app_client: httpx.AsyncClient) -> None:
    response = await app_client.get("/ping")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    # Plain HTTP → no HSTS (it would lock out non-TLS clients).
    assert "Strict-Transport-Security" not in response.headers


async def test_hsts_only_over_https(app_client: httpx.AsyncClient) -> None:
    response = await app_client.get(
        "/ping", headers={"X-Forwarded-Proto": "https"}
    )
    assert response.headers["Strict-Transport-Security"] == (
        "max-age=63072000; includeSubDomains"
    )


async def test_cross_site_mutation_blocked(app_client: httpx.AsyncClient) -> None:
    """Browser sending Sec-Fetch-Site: cross-site is rejected before the handler."""
    response = await app_client.post(
        "/echo", headers={"Sec-Fetch-Site": "cross-site"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Cross-site request blocked"


async def test_same_origin_mutation_allowed(app_client: httpx.AsyncClient) -> None:
    response = await app_client.post(
        "/echo",
        headers={
            "Sec-Fetch-Site": "same-origin",
            "Origin": "http://test",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}


async def test_foreign_origin_without_fetch_site_blocked(
    app_client: httpx.AsyncClient,
) -> None:
    """Origin not in CORS_ORIGINS and not same-host → 403."""
    response = await app_client.post("/echo", headers={"Origin": "http://evil.com"})
    assert response.status_code == 403


async def test_allowed_cors_origin_passes(app_client: httpx.AsyncClient) -> None:
    """Origin in settings.CORS_ORIGINS is permitted."""
    response = await app_client.post(
        "/echo", headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200


async def test_same_host_origin_passes(app_client: httpx.AsyncClient) -> None:
    response = await app_client.post(
        "/echo", headers={"Origin": "http://test"}
    )
    assert response.status_code == 200


async def test_non_browser_client_passes(app_client: httpx.AsyncClient) -> None:
    """No Sec-Fetch-Site, no Origin (curl / eval script) → unaffected."""
    response = await app_client.post("/echo")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
