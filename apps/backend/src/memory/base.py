"""Abstract memory provider interface."""

from abc import ABC, abstractmethod
from typing import Any


class MemoryProvider(ABC):
    """Interface for key-value memory backends.

    Implementations may store data in Postgres, Redis, AgentDB, or any
    other store that supports key-value access with basic search.
    """

    @abstractmethod
    async def store(self, key: str, value: Any) -> None:
        """Persist a value under the given key.

        Args:
            key: Unique identifier for the memory entry.
            value: Arbitrary data to store.
        """

    @abstractmethod
    async def retrieve(self, key: str) -> Any | None:
        """Fetch a previously stored value by key.

        Args:
            key: The key to look up.

        Returns:
            The stored value, or None if not found.
        """

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove a memory entry by key.

        Args:
            key: The key to delete.
        """

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search memory entries by content.

        Args:
            query: Free-text search string.
            limit: Maximum number of results.

        Returns:
            A list of matching entries with at least ``key`` and ``value``.
        """
