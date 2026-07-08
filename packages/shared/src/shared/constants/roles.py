"""User role enumeration for authorization."""

from __future__ import annotations

from enum import Enum


class UserRole(str, Enum):
    """Authorisation roles available on the platform.

    Roles follow a hierarchical permission model:
    ``ADMIN > USER > VIEWER``.
    """

    ADMIN = "admin"
    """Full system access, including user and tenant management."""

    USER = "user"
    """Standard user with read/write access to own resources."""

    VIEWER = "viewer"
    """Read-only access to shared resources."""
