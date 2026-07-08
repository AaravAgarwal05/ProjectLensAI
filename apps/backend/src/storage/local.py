"""Local-filesystem storage provider."""

import logging
from pathlib import Path

from src.config.settings import get_settings
from src.storage.base import StorageProvider

logger = logging.getLogger(__name__)


class LocalStorageProvider(StorageProvider):
    """Stores and retrieves files on the local filesystem.

    All files are placed under a configurable base directory. Sub-directories
    are created automatically as needed.
    """

    def __init__(self, base_path: str | None = None) -> None:
        settings = get_settings()
        self._base = Path(base_path or settings.STORAGE_LOCAL_PATH).resolve()
        self._base.mkdir(parents=True, exist_ok=True)
        logger.info("Local storage initialised at %s", self._base)

    def _resolve(self, path: str) -> Path:
        """Resolve a logical path to an absolute filesystem path.

        Raises:
            ValueError: If the resolved path escapes the base directory.
        """
        resolved = (self._base / path).resolve()
        if not str(resolved).startswith(str(self._base)):
            raise ValueError(f"Path traversal detected: {path}")
        return resolved

    async def store(self, file_path: str, content: bytes) -> str:
        target = self._resolve(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        logger.debug("Stored %d bytes at %s", len(content), target)
        return str(target.relative_to(self._base))

    async def retrieve(self, path: str) -> bytes:
        target = self._resolve(path)
        return target.read_bytes()

    async def delete(self, path: str) -> None:
        target = self._resolve(path)
        if target.exists():
            target.unlink()
            logger.debug("Deleted %s", target)

    async def exists(self, path: str) -> bool:
        target = self._resolve(path)
        return target.exists()
