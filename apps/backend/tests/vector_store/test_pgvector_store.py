"""Tests for PgVectorStore provider (no pgvector required)."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from src.ai_core.vector_store.models import VectorDocument, VectorMetadata
from src.ai_core.vector_store.providers.pgvector_store import PgVectorStore


class _FakePool:
    """Fake asyncpg pool — acquire() yields a fake connection."""

    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _AcquireCM(self._conn)


class _AcquireCM:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *exc):
        return False


class _FakeConn:
    """Fake asyncpg connection: fetch/fetchrow/fetchval/execute are AsyncMocks."""

    def __init__(self, fetch_rows=None, fetchval_result=None, execute_result="DELETE 2"):
        self.fetch = AsyncMock(return_value=fetch_rows or [])
        self.fetchval = AsyncMock(return_value=fetchval_result)
        # [False] → collection_exists reports "not exists" so create_collection proceeds
        self.fetchrow = AsyncMock(return_value=[False])
        self.execute = AsyncMock(return_value=execute_result)


def _make_docs():
    return [
        VectorDocument(
            chunk_id="c1",
            vector=[0.1, 0.2, 0.3],
            dimensions=3,
            text="chunk one",
            metadata=VectorMetadata(
                chunk_id="c1",
                report_id="r1",
                version_id="v1",
                embedding_model="test",
                embedding_provider="test",
                extra={"title": "Doc A", "page_number": 2, "section_name": "Intro"},
            ),
        ),
        VectorDocument(
            chunk_id="c2",
            vector=[0.4, 0.5, 0.6],
            dimensions=3,
            text="chunk two",
            metadata=VectorMetadata(
                chunk_id="c2",
                report_id="r1",
                version_id="v1",
                embedding_model="test",
                embedding_provider="test",
                extra={"title": "Doc A", "page_number": 3, "section_name": "Body"},
            ),
        ),
    ]


def _store_with_pool(conn):
    store = PgVectorStore()
    store._pool = _FakePool(conn)  # bypass _get_pool entirely
    return store


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

    def test_configure_dimensions(self):
        store = PgVectorStore()
        store.configure({"dimensions": 768})
        assert store._dimensions == 768

    async def test_create_collection_uses_configured_dimensions(self):
        store = PgVectorStore(dimensions=8)
        conn = _FakeConn()
        store._pool = _FakePool(conn)

        result = await store.create_collection("report_r1")

        assert result is True
        create_sql = conn.execute.call_args_list[0][0][0]
        assert "vector(8)" in create_sql
        assert "content TEXT DEFAULT ''" in create_sql

    async def test_insert_writes_content_and_metadata(self):
        store = _store_with_pool(_FakeConn())
        docs = _make_docs()

        count = await store.insert("report_r1", docs)

        assert count == 2
        args = conn_args(store, "report_r1")
        # INSERT args: sql, chunk_id, vector, content, report_id, version_id, model, provider, metadata-json
        assert args[0][3] == "chunk one"  # content column
        assert '"page_number": 2' in args[0][8]  # metadata JSONB holds extra
        assert '"title": "Doc A"' in args[0][8]

    async def test_update_writes_content_and_metadata(self):
        store = _store_with_pool(_FakeConn())
        docs = _make_docs()

        count = await store.update("report_r1", docs)

        assert count == 2
        args = conn_args(store, "report_r1")
        # UPDATE args: sql, vector, content, report_id, version_id, model, provider, metadata-json, chunk_id
        assert args[0][2] == "chunk one"  # content column
        assert '"page_number": 2' in args[0][7]

    async def test_query_returns_flat_meta_hits(self):
        conn = _FakeConn(
            fetch_rows=[
                {
                    "chunk_id": "c1",
                    "content": "chunk one",
                    "metadata": {"title": "Doc A", "page_number": 2},
                    "report_id": "r1",
                    "version_id": "v1",
                    "embedding_model": "test",
                    "embedding_provider": "test",
                    "score": 0.9,
                },
                {
                    "chunk_id": "c2",
                    "content": "chunk two",
                    "metadata": {"title": "Doc A", "page_number": 3},
                    "report_id": "r1",
                    "version_id": "v1",
                    "embedding_model": "test",
                    "embedding_provider": "test",
                    "score": 0.4,
                },
            ]
        )
        store = _store_with_pool(conn)

        hits = await store.query("report_r1", [0.1, 0.2, 0.3], top_k=5)

        assert len(hits) == 2
        assert hits[0].chunk_id == "c1"
        assert hits[0].score == 0.9
        # Flat meta merges columns + JSONB extra
        assert hits[0].metadata["report_id"] == "r1"
        assert hits[0].metadata["title"] == "Doc A"
        assert hits[0].metadata["page_number"] == 2
        assert hits[1].score < hits[0].score
        # ORDER BY vector <=> $1 LIMIT $2 — distance operator + limit
        query_sql = conn.fetch.call_args_list[0][0][0]
        assert "<=>" in query_sql
        assert "LIMIT $2" in query_sql

    async def test_fetch_all_returns_hits(self):
        conn = _FakeConn(
            fetch_rows=[
                {"chunk_id": "c1", "content": "chunk one", "metadata": {"title": "Doc A"}},
                {"chunk_id": "c2", "content": "chunk two", "metadata": {"title": "Doc A"}},
            ]
        )
        store = _store_with_pool(conn)

        hits = await store.fetch_all("report_r1")

        assert len(hits) == 2
        assert {h.chunk_id for h in hits} == {"c1", "c2"}
        assert hits[0].content == "chunk one"
        assert hits[0].metadata["title"] == "Doc A"
        assert hits[0].score == 0.0


def conn_args(store, collection):
    """Return the positional args of the last INSERT/UPDATE execute per doc.

    The fake pool's connection is shared, so we inspect the execute calls made
    for the given statement type (INSERT vs UPDATE has distinct arg counts).
    """
    conn = store._pool._conn
    calls = conn.execute.call_args_list
    return [call[0] for call in calls]
