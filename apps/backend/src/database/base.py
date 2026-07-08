"""SQLAlchemy declarative base for all ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Abstract base class for all database models.

    Every ORM model in the application should inherit from this class.
    """

    pass
