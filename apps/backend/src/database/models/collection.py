"""Collection ORM model."""

from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship

from src.database.base import Base
from src.database.mixins import TimestampMixin, UUIDMixin


class Collection(UUIDMixin, TimestampMixin, Base):
    """A named grouping of reports."""

    __tablename__ = "collections"
    __allow_unmapped__ = True

    name: Column[str] = Column(String, nullable=False, unique=True, index=True)
    description: Column[str | None] = Column(Text, nullable=True)

    reports = relationship(
        "Report",
        secondary="collection_reports",
        back_populates="collections",
    )
