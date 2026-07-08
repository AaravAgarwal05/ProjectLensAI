"""Data transfer object for pagination parameters."""

from __future__ import annotations

from pydantic import Field
from pydantic.main import BaseModel


class PaginationDTO(BaseModel):
    """DTO carrying pagination parameters for list queries.

    Attributes:
        page: Page number (1-indexed, defaults to 1).
        page_size: Number of items per page (defaults to 20).
        total: Optional total item count (populated by the service layer).
    """

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    total: int | None = None

    @property
    def offset(self) -> int:
        """Compute the offset for database queries based on the current page."""
        return (self.page - 1) * self.page_size
