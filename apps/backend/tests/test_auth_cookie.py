"""Tests for HttpOnly-cookie JWT auth.

The web app authenticates via a cookie that JavaScript can never read;
the Bearer header is kept for API tooling / the eval script. These tests
verify the cookie is set on register and that ``/auth/me`` resolves the
user from the cookie alone.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from src.database import models  # noqa: F401


def _user_orm():
    """A real User ORM instance (no DB) to return from the fake factory."""
    from src.database.models import User

    return User(
        email="a@b.com",
        name="Test",
        hashed_password="x",
        role="user",
        is_active=True,
        token_version=0,
    )


async def test_register_sets_httponly_auth_cookie(
    api_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.api.rate_limiter import limiter
    from src.database import session as db_session

    async def _fake_factory():
        s = AsyncMock()
        s.commit = AsyncMock()
        s.rollback = AsyncMock()
        s.close = AsyncMock()
        s.flush = AsyncMock()
        s.refresh = AsyncMock()
        s.add = AsyncMock()
        yield s

    # get_current_user opens its own session via the factory.
    monkeypatch.setattr(db_session, "async_session_factory", _fake_factory)
    # register is rate-limited (5/hour, Redis-backed) — disable for the test.
    monkeypatch.setattr(limiter, "enabled", False)

    response = await api_client.post(
        "/api/v1/auth/register",
        json={"email": "a@b.com", "password": "supersecret1", "name": "Test"},
    )

    assert response.status_code == 200
    assert response.json()["token"]

    # Cookie is present, HttpOnly and SameSite=Lax — invisible to JS.
    cookie = response.headers.get("set-cookie", "")
    assert "auth_token=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert response.cookies.get("auth_token")


async def test_me_resolves_user_from_cookie(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A request carrying only the cookie (no Authorization header) is authed."""
    from src.database import session as db_session

    user = _user_orm()
    result = MagicMock()
    result.scalar_one_or_none.return_value = user

    def _fake_factory():
        s = AsyncMock()
        s.__aenter__.return_value = s  # async with factory() as db → db is s
        s.execute = AsyncMock(return_value=result)
        s.commit = AsyncMock()
        s.rollback = AsyncMock()
        s.close = AsyncMock()
        return s

    monkeypatch.setattr(db_session, "async_session_factory", _fake_factory)

    from src.auth.jwt import create_access_token

    token = create_access_token({"sub": "user-1", "tv": 0})

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Cookie": f"auth_token={token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "a@b.com"


async def test_me_401_without_token(client: AsyncClient) -> None:
    """No bearer header and no cookie → 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
