"""CollectionReport association table for the many-to-many relationship."""

from sqlalchemy import Column, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID

from src.database.base import Base


class CollectionReport(Base):
    """Links reports to collections in a many-to-many relationship."""

    __tablename__ = "collection_reports"
    __allow_unmapped__ = True

    collection_id: Column = Column(
        UUID(as_uuid=True),
        ForeignKey("collections.id", ondelete="CASCADE"),
        primary_key=True,
    )
    report_id: Column = Column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Column = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
