"""Indexing engine — orchestrates the chunk-to-index lifecycle.

Pipeline:
    EmbeddedChunk → Batch → VectorStore → IndexingResult

Supports batch indexing, batch deletion, reindexing, validation, and retry.
"""

from __future__ import annotations

import logging
import time

from src.ai_core.embedding.models import EmbeddedChunk
from src.ai_core.vector_store.base import VectorStore
from src.ai_core.vector_store.configuration import VectorStoreConfiguration
from src.ai_core.vector_store.exceptions import VectorStoreError
from src.ai_core.vector_store.factory import VectorStoreFactory
from src.ai_core.vector_store.models import (
    DeleteResult,
    IndexingResult,
    IndexingStatistics,
    VectorDocument,
    VectorMetadata,
)
from src.ai_core.vector_store.validation import VectorStoreValidationEngine

logger = logging.getLogger(__name__)

_RETRYABLE_EXCEPTIONS = (ConnectionError, TimeoutError, VectorStoreError)


class IndexingEngine:
    """Orchestrates the chunk-to-index lifecycle.

    Typical usage::

        engine = IndexingEngine(store)
        result = await engine.index(chunks)
    """

    def __init__(
        self,
        store: VectorStore | None = None,
        factory: VectorStoreFactory | None = None,
        config: VectorStoreConfiguration | None = None,
        validation: VectorStoreValidationEngine | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        self._store = store
        self._factory = factory or VectorStoreFactory()
        self._config = config or VectorStoreConfiguration.default()
        self._validation = validation
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    @property
    def store(self) -> VectorStore | None:
        return self._store

    async def index(
        self,
        chunks: list[EmbeddedChunk],
        collection: str | None = None,
        store: VectorStore | None = None,
        batch_size: int | None = None,
    ) -> IndexingResult:
        """Index a list of embedded chunks.

        Args:
            chunks: ``EmbeddedChunk`` objects to index.
            collection: Target collection (default from config).
            store: Override store (default from config).
            batch_size: Override batch size (default from config).

        Returns:
            An ``IndexingResult``.
        """
        start = time.monotonic()
        result = IndexingResult()

        resolved_store = store or self._store
        if resolved_store is None:
            resolved_store = self._factory.create_from_config(self._config)
        self._store = resolved_store

        resolved_collection = collection or self._config.collection_name
        result.collection_name = resolved_collection

        batch_sz = batch_size or self._config.batch_size

        if not chunks:
            result.warnings.append("No chunks provided")
            result.successful = True
            return result

        # Ensure collection exists
        try:
            exists = await resolved_store.collection_exists(resolved_collection)
            if not exists:
                await resolved_store.create_collection(resolved_collection)
        except Exception as exc:
            result.errors.append(f"Failed to ensure collection: {exc}")
            result.successful = False
            return result

        # Split into batches
        batches = [chunks[i : i + batch_sz] for i in range(0, len(chunks), batch_sz)]

        all_docs: list[VectorDocument] = []

        for batch_idx, batch in enumerate(batches):
            docs = [_to_vector_doc(c) for c in batch]
            success = False

            for attempt in range(1, self._max_retries + 1):
                try:
                    inserted = await resolved_store.insert(resolved_collection, docs)
                    if inserted == len(docs):
                        success = True
                        all_docs.extend(docs)
                        break

                    if attempt < self._max_retries:
                        wait = self._retry_delay * attempt
                        logger.info(
                            "Retry %d/%d for batch %d after %ds",
                            attempt,
                            self._max_retries,
                            batch_idx,
                            wait,
                        )
                        await _sleep(wait)
                except _RETRYABLE_EXCEPTIONS:
                    if attempt < self._max_retries:
                        wait = self._retry_delay * attempt
                        await _sleep(wait)
                    else:
                        result.errors.append(
                            f"Batch {batch_idx} failed after " f"{self._max_retries} retries"
                        )
                except Exception as exc:
                    result.errors.append(f"Batch {batch_idx} failed: {exc}")
                    break

            if not success:
                result.successful = False

        # Validation
        if self._validation:
            vr = self._validation.validate_indexing(resolved_collection, all_docs)
            if vr.errors:
                result.errors.extend(vr.errors)
                result.successful = False
            for w in vr.warnings:
                if w not in result.warnings:
                    result.warnings.append(w)

        # Statistics
        elapsed = time.monotonic() - start
        n_docs = len(all_docs)
        result.statistics = IndexingStatistics(
            total_documents=len(chunks),
            successful=n_docs,
            failed=len(chunks) - n_docs,
            total_time=elapsed,
            throughput=n_docs / elapsed if elapsed > 0 else 0.0,
            avg_latency=elapsed / len(batches) if batches else 0.0,
        )
        result.documents = all_docs

        return result

    async def _resolve_store(self, store: VectorStore | None = None) -> VectorStore:
        if store is not None:
            return store
        if self._store is not None:
            return self._store
        self._store = self._factory.create_from_config(self._config)
        return self._store

    async def delete(
        self,
        chunk_ids: list[str],
        collection: str | None = None,
        store: VectorStore | None = None,
    ) -> DeleteResult:
        """Delete specific chunks from the index."""
        resolved_store = await self._resolve_store(store)
        resolved_collection = collection or self._config.collection_name

        try:
            deleted = await resolved_store.delete(resolved_collection, chunk_ids=chunk_ids)
            return DeleteResult(collection_name=resolved_collection, deleted_count=deleted)
        except Exception as exc:
            return DeleteResult(
                collection_name=resolved_collection,
                successful=False,
                errors=[str(exc)],
            )

    async def delete_by_report(
        self,
        report_id: str,
        collection: str | None = None,
        store: VectorStore | None = None,
    ) -> DeleteResult:
        """Delete all vectors for a report."""
        resolved_store = await self._resolve_store(store)
        resolved_collection = collection or self._config.collection_name
        return await resolved_store.delete_by_report(resolved_collection, report_id)

    async def delete_by_version(
        self,
        version_id: str,
        collection: str | None = None,
        store: VectorStore | None = None,
    ) -> DeleteResult:
        """Delete all vectors for a version."""
        resolved_store = await self._resolve_store(store)
        resolved_collection = collection or self._config.collection_name
        return await resolved_store.delete_by_version(resolved_collection, version_id)

    async def reindex(
        self,
        chunks: list[EmbeddedChunk],
        collection: str | None = None,
        store: VectorStore | None = None,
    ) -> IndexingResult:
        """Drop and reindex — delete collection first, then index."""
        resolved_store = await self._resolve_store(store)
        resolved_collection = collection or self._config.collection_name

        import contextlib

        with contextlib.suppress(Exception):
            await resolved_store.delete_collection(resolved_collection)

        return await self.index(chunks, collection, store)

    async def count(
        self,
        collection: str | None = None,
        store: VectorStore | None = None,
    ) -> int:
        """Return the document count for a collection."""
        resolved_store = await self._resolve_store(store)
        resolved_collection = collection or self._config.collection_name
        return await resolved_store.count(resolved_collection)


def _to_vector_doc(chunk: EmbeddedChunk) -> VectorDocument:
    """Convert an ``EmbeddedChunk`` to a ``VectorDocument``."""
    return VectorDocument(
        chunk_id=chunk.chunk_id,
        vector=chunk.vector.vector,
        dimensions=chunk.dimensions,
        metadata=VectorMetadata(
            chunk_id=chunk.chunk_id,
            report_id=chunk.metadata.extra.get("report_id", ""),
            version_id=chunk.metadata.extra.get("version_id", ""),
            embedding_model=chunk.embedding_model,
            embedding_provider=chunk.embedding_provider,
            created_at=chunk.created_at,
            extra={
                k: v
                for k, v in chunk.metadata.extra.items()
                if k not in ("report_id", "version_id")
            },
        ),
    )


async def _sleep(seconds: float) -> None:
    """Async sleep."""
    import asyncio

    await asyncio.sleep(seconds)
