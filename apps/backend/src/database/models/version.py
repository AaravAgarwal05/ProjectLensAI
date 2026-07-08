"""ReportVersion ORM model."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.base import Base
from src.database.mixins import UUIDMixin


class ReportVersion(UUIDMixin, Base):
    """A specific version of a report file."""

    __tablename__ = "report_versions"
    __allow_unmapped__ = True

    report_id: Column = Column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Column[int] = Column(Integer, nullable=False)
    storage_path: Column[str] = Column(String, nullable=False)
    original_filename: Column[str] = Column(String, nullable=False)
    mime_type: Column[str] = Column(String, nullable=False)
    checksum: Column[str] = Column(String, nullable=False)
    file_size: Column[int] = Column(Integer, nullable=False)
    created_at: Column = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("report_id", "version_number"),
    )

    report = relationship("Report", back_populates="versions")
