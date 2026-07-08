"""Pydantic models for user and user-preferences entities."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field
from pydantic.main import BaseModel


class UserPreferences(BaseModel):
    """User preference settings.

    Attributes:
        theme: UI theme (``"light"`` or ``"dark"``).
        language: Preferred ISO language code.
        notifications_enabled: Whether push/email notifications are active.
    """

    theme: str = "light"
    language: str = "en"
    notifications_enabled: bool = True


class User(BaseModel):
    """A platform user account.

    Attributes:
        id: Unique user identifier.
        email: User email address.
        username: Display / login username.
        role: Authorization role (defaults to ``"user"``).
        is_active: Whether the account is active.
        preferences: User preference settings.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
    """

    model_config = {"frozen": True}

    id: UUID = Field(default_factory=uuid4)
    email: str
    username: str
    role: str = "user"
    is_active: bool = True
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    created_at: datetime
    updated_at: datetime
