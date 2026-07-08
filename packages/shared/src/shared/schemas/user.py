"""API schemas for user registration, profile update, and response."""

from __future__ import annotations

from pydantic.main import BaseModel

from shared.models.user import User


class UserCreate(BaseModel):
    """Request schema for creating (registering) a new user.

    Attributes:
        email: User email address.
        username: Display / login username.
        password: Plain-text password (hashed server-side).
    """

    email: str
    username: str
    password: str


class UserUpdate(BaseModel):
    """Request schema for updating an existing user's profile.

    All fields are optional; only provided fields are applied.
    """

    email: str | None = None
    username: str | None = None
    preferences: dict | None = None


class UserResponse(BaseModel):
    """Response schema for user operations.

    Attributes:
        user: The user object.
        token: Optional JWT token (included on registration / login).
    """

    user: User
    token: str | None = None
