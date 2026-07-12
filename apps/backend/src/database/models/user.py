"""User ORM model for authentication."""

from sqlalchemy import Boolean, Column, String

from src.database.base import Base
from src.database.mixins import TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    """Registered user account."""

    __tablename__ = "users"
    __allow_unmapped__ = True

    email: Column[str] = Column(String(255), nullable=False, unique=True, index=True)
    name: Column[str] = Column(String(255), nullable=False)
    hashed_password: Column[str] = Column(String(255), nullable=False)
    role: Column[str] = Column(String(50), nullable=False, default="user")
    is_active: Column[bool] = Column(Boolean, nullable=False, default=True)
