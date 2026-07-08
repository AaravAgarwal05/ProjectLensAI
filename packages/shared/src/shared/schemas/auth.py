"""API schemas for authentication flows (login, register, token refresh)."""

from __future__ import annotations

from pydantic.main import BaseModel


class LoginRequest(BaseModel):
    """Request schema for user login.

    Attributes:
        email: User email address.
        password: User password.
    """

    email: str
    password: str


class RegisterRequest(BaseModel):
    """Request schema for user registration.

    Attributes:
        email: User email address.
        username: Desired username.
        password: Desired password.
    """

    email: str
    username: str
    password: str


class TokenResponse(BaseModel):
    """Response schema for successful authentication.

    Attributes:
        access_token: JWT access token.
        token_type: Token type (defaults to ``"bearer"``).
        expires_in: Token lifetime in seconds.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    """Request schema for refreshing an expired access token.

    Attributes:
        refresh_token: The refresh token value.
    """

    refresh_token: str
