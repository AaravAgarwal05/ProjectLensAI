"""Generic repository interface."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(ABC, Generic[T]):
    """Abstract generic repository for CRUD operations.

    Type parameter *T* must be a subclass of ``pydantic.BaseModel``.
    """

    @abstractmethod
    def get(self, id: str) -> T | None:
        """Retrieve a single entity by its identifier."""

    @abstractmethod
    def list(self, offset: int = 0, limit: int = 100) -> list[T]:
        """List entities with pagination support."""

    @abstractmethod
    def create(self, data: T) -> T:
        """Create a new entity and return it."""

    @abstractmethod
    def update(self, id: str, data: T) -> T:
        """Update an existing entity and return it."""

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete an entity by identifier. Returns True if deleted."""
