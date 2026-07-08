"""Supabase Storage provider using the server-side service_role key."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.api.exceptions import ProjectLensError
from src.storage.base import StorageProvider

if TYPE_CHECKING:
    from supabase import Client

logger = logging.getLogger(__name__)

try:
    from supabase import create_client as _supabase_create_client

    _supabase_available = True
except ImportError:  # pragma: no cover
    _supabase_available = False
    _supabase_create_client = None  # type: ignore[assignment]


class SupabaseStorageProvider(StorageProvider):
    """Stores and retrieves files in a Supabase Storage bucket.

    Uses the service_role key for server-side operations so that bucket
    management and object read/write bypass Row Level Security.
    """

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        bucket_name: str = "reports",
    ) -> None:
        self._supabase_url = supabase_url
        self._supabase_key = supabase_key
        self._bucket_name = bucket_name
        self._client: Client | None = None
        self._bucket_ensured = False

    # ------------------------------------------------------------------
    # Client
    # ------------------------------------------------------------------

    def _get_client(self) -> Client:
        """Lazy-initialise and return the Supabase client instance."""
        if self._client is not None:
            return self._client

        if not _supabase_available:
            raise ProjectLensError(
                message="Supabase package is not installed. "
                "Run `pip install supabase` or add it to project dependencies.",
                code="supabase_not_installed",
            )

        if not self._supabase_url or not self._supabase_key:
            raise ProjectLensError(
                message="Supabase URL and key must be configured.",
                code="supabase_misconfigured",
            )

        self._client = _supabase_create_client(
            self._supabase_url,
            self._supabase_key,
        )
        logger.info("Supabase client initialised for bucket '%s'", self._bucket_name)
        return self._client

    def _ensure_bucket(self) -> None:
        """Create the storage bucket if it does not already exist."""
        if self._bucket_ensured:
            return

        client = self._get_client()
        try:
            client.storage.get_bucket(self._bucket_name)
            logger.debug("Bucket '%s' already exists", self._bucket_name)
        except Exception:
            try:
                client.storage.create_bucket(self._bucket_name)
                logger.info("Created bucket '%s'", self._bucket_name)
            except Exception as exc:
                raise ProjectLensError(
                    message=f"Failed to create Supabase bucket '{self._bucket_name}': {exc}",
                    code="bucket_creation_failed",
                ) from exc

        self._bucket_ensured = True

    # ------------------------------------------------------------------
    # Storage operations
    # ------------------------------------------------------------------

    async def store(self, file_path: str, content: bytes) -> str:
        """Upload content to Supabase Storage.

        Returns:
            The path that can be used to retrieve or delete the object.
        """
        self._ensure_bucket()
        client = self._get_client()

        try:
            # Strip a leading slash so the path is consistent.
            clean_path = file_path.lstrip("/")
            client.storage.from_(self._bucket_name).upload(
                clean_path,
                content,
                {"content-type": "application/octet-stream"},
            )
            logger.debug("Stored %d bytes at '%s'", len(content), clean_path)
            return clean_path
        except Exception as exc:
            raise ProjectLensError(
                message=f"Failed to upload to Supabase Storage: {exc}",
                code="storage_upload_failed",
            ) from exc

    async def retrieve(self, path: str) -> bytes:
        """Download content from Supabase Storage."""
        client = self._get_client()
        try:
            data: bytes = client.storage.from_(self._bucket_name).download(path)
            return data
        except Exception as exc:
            raise ProjectLensError(
                message=f"Failed to download from Supabase Storage: {exc}",
                code="storage_download_failed",
            ) from exc

    async def delete(self, path: str) -> None:
        """Remove an object from Supabase Storage."""
        client = self._get_client()
        try:
            client.storage.from_(self._bucket_name).remove([path])
            logger.debug("Deleted '%s'", path)
        except Exception as exc:
            raise ProjectLensError(
                message=f"Failed to delete from Supabase Storage: {exc}",
                code="storage_delete_failed",
            ) from exc

    async def exists(self, path: str) -> bool:
        """Check whether an object exists in Supabase Storage.

        Lists the parent prefix and checks for the target filename. This is a
        lightweight operation compared to downloading the full object.
        """
        client = self._get_client()
        try:
            parent_prefix = path.rsplit("/", 1)[0] if "/" in path else ""
            target_name = path.rsplit("/", 1)[-1]
            objects = client.storage.from_(self._bucket_name).list(parent_prefix)
            return any(o.get("name") == target_name for o in objects)
        except Exception:
            return False
