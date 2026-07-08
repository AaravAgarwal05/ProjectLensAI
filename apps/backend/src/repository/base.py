"""Generic SQLAlchemy repository with common CRUD operations."""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic async repository providing standard CRUD methods.

    Type-param ``ModelT`` must be a SQLAlchemy declarative model.
    """

    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get(self, ident: Any) -> ModelT | None:
        """Retrieve a single record by primary-key value."""
        return await self.session.get(self.model, ident)

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> Sequence[ModelT]:
        """Retrieve a paginated, optionally filtered list of records."""
        stmt = select(self.model)

        for attr, value in filters.items():
            column = getattr(self.model, attr, None)
            if column is not None:
                stmt = stmt.where(column == value)

        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, **filters: Any) -> int:
        """Count records matching the given filters."""
        stmt = select(func.count(self.model.id))

        for attr, value in filters.items():
            column = getattr(self.model, attr, None)
            if column is not None:
                stmt = stmt.where(column == value)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, **kwargs: Any) -> ModelT:
        """Create and return a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, ident: Any, **kwargs: Any) -> ModelT | None:
        """Update a record by primary-key value and return it."""
        instance = await self.get(ident)
        if instance is None:
            return None

        for key, value in kwargs.items():
            setattr(instance, key, value)

        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, ident: Any) -> bool:
        """Delete a record by primary-key value. Returns True if deleted."""
        instance = await self.get(ident)
        if instance is None:
            return False

        await self.session.delete(instance)
        await self.session.flush()
        return True
