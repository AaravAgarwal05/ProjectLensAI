"""Report ORM model."""

from sqlalchemy import ARRAY, Column, Integer, String, Text
from sqlalchemy.orm import relationship

from src.database.base import Base
from src.database.mixins import TimestampMixin, UUIDMixin


class Report(UUIDMixin, TimestampMixin, Base):
    """A report document with metadata and storage information."""

    __tablename__ = "reports"
    __allow_unmapped__ = True

    title: Column[str] = Column(String, nullable=False, index=True)
    description: Column[str | None] = Column(Text, nullable=True)
    department: Column[str | None] = Column(String, nullable=True)
    author: Column[str | None] = Column(String, nullable=True, index=True)
    tags: Column[list[str] | None] = Column(ARRAY(Text), nullable=True)
    visibility: Column[str] = Column(String, nullable=False, default="private")
    year: Column[int | None] = Column(Integer, nullable=True)
    status: Column[str] = Column(String, nullable=False, default="draft", index=True)
    storage_provider: Column[str] = Column(String, nullable=False, default="supabase")
    storage_path: Column[str | None] = Column(String, nullable=True)
    original_filename: Column[str | None] = Column(String, nullable=True)
    mime_type: Column[str | None] = Column(String, nullable=True)
    checksum: Column[str | None] = Column(String, nullable=True)
    file_size: Column[int | None] = Column(Integer, nullable=True)

    # Relationships
    versions = relationship(
        "ReportVersion",
        back_populates="report",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    collections = relationship(
        "Collection",
        secondary="collection_reports",
        back_populates="reports",
    )
