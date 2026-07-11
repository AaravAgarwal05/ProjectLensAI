"""Tests for PgVectorStore provider (no pgvector required)."""

import asyncio

import pytest

from src.ai_core.vector_store.models import VectorDocument, VectorMetadata
from src.ai_core.vector_store.providers.pgvector_store import PgVectorStore


class TestPgVectorStore:
    def test_provider_name(self):
        store = PgVectorStore()
        assert store.store_name == "pgvector"

    async def test_health_check_no_connection(self):
        store = PgVectorStore(dsn="postgres://localhost:59999/nonexistent")
        healthy = await store.health_check()
        assert healthy is False

    async def test_create_collection_no_connection(self):
        store = PgVectorStore(dsn="postgres://localhost:59999/nonexistent")
        try:
            result = await store.create_collection("test", dimensions=4)
            assert result is False
        except (RuntimeError, ConnectionRefusedError, OSError):
            pass
        except asyncio.TimeoutError:
            pass

    async def test_collection_exists_no_connection(self):
        store = PgVectorStore(dsn="postgres://localhost:59999/nonexistent")
        exists = await store.collection_exists("test")
        assert exists is False

    async def test_insert_no_connection(self):
        store = PgVectorStore(dsn="postgres://localhost:59999/nonexistent")
        docs = [
            VectorDocument(
                chunk_id="c1",
                vector=[0.1, 0.2],
                dimensions=2,
                metadata=VectorMetadata(chunk_id="c1"),
            )
        ]
        try:
            count = await store.insert("test", docs)
            assert count == 0
        except (RuntimeError, ConnectionRefusedError, OSError):
            pass
        except asyncio.TimeoutError:
            pass

    async def test_delete_by_report_no_connection(self):
        store = PgVectorStore(dsn="postgres://localhost:59999/nonexistent")
        result = await store.delete_by_report("test", "r1")
        assert result.successful is False
        assert len(result.errors) > 0

    async def test_count_no_connection(self):
        store = PgVectorStore(dsn="postgres://localhost:59999/nonexistent")
        try:
            count = await store.count("test")
            assert count == 0
        except (RuntimeError, ConnectionRefusedError, OSError):
            pass
        except asyncio.TimeoutError:
            pass

    def test_configure(self):
        store = PgVectorStore()
        store.configure({"dsn": "postgres://localhost:5432/db"})
        assert store._dsn == "postgres://localhost:5432/db"
        assert store._pool is None

    def test_configure_schema(self):
        store = PgVectorStore()
        store.configure({"schema": "custom"})
        assert store._schema == "custom"
