"""Authentication endpoints (register, login, token refresh)."""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_settings
from src.config.settings import AppSettings

router = APIRouter()


@router.post("/register")
async def register(
    settings: AppSettings = Depends(get_settings),
) -> dict:
    """Register a new user account.

    This is a placeholder — full implementation will follow.
    """
    return {"message": "Registration endpoint — not yet implemented"}


@router.post("/login")
async def login(
    settings: AppSettings = Depends(get_settings),
) -> dict:
    """Authenticate a user and return access/refresh tokens.

    This is a placeholder — full implementation will follow.
    """
    return {"message": "Login endpoint — not yet implemented"}


@router.post("/refresh")
async def refresh_token(
    settings: AppSettings = Depends(get_settings),
) -> dict:
    """Refresh an expired access token using a valid refresh token.

    This is a placeholder — full implementation will follow.
    """
    return {"message": "Token refresh endpoint — not yet implemented"}
