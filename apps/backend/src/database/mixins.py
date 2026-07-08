"""Reusable SQLAlchemy mixins for common model fields."""

import uuid

from sqlalchemy import Column, DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_mixin


@declarative_mixin
class TimestampMixin:
    """Adds created_at and updated_at timestamp columns.

    Both columns use server-side defaults so they work reliably with async.
    """

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


@declarative_mixin
class UUIDMixin:
    """Adds a UUID primary key column with a server-side default."""

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
        index=True,
    )
