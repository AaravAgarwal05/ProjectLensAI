"""Abstract storage provider interface."""

from abc import ABC, abstractmethod


class StorageProvider(ABC):
    """Interface for file storage backends.

    Implementations handle persistence of raw file content (documents,
    images, etc.) to local disk, S3, GCS, or any other backend.
    """

    @abstractmethod
    async def store(self, file_path: str, content: bytes) -> str:
        """Persist content at the given path.

        Args:
            file_path: Logical path or key for the stored object.
            content: Raw bytes to persist.

        Returns:
            The path (or URI) at which the content was stored.
        """

    @abstractmethod
    async def retrieve(self, path: str) -> bytes:
        """Read content from storage.

        Args:
            path: Path or key previously returned by ``store``.

        Returns:
            Raw bytes of the stored object.
        """

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Remove a stored object.

        Args:
            path: Path or key of the object to delete.
        """

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check whether a stored object exists.

        Args:
            path: Path or key to check.

        Returns:
            True if the object exists, False otherwise.
        """
