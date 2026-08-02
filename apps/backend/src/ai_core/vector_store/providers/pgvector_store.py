"""PgVector vector-store provider.

Uses PostgreSQL with the pgvector extension.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.ai_core.vector_store.base import VectorStore
from src.ai_core.vector_store.models import DeleteResult, VectorDocument, VectorHit

logger = logging.getLogger(__name__)


class PgVectorStore(VectorStore):
    """Vector-store provider wrapping PostgreSQL + pgvector.

    Configuration:
        dsn: PostgreSQL connection string.
        schema: Database schema name (default ``"vector_store"``).
        pool_size: Connection pool size (default 5).
        dimensions: Embedding vector dimensions (default 384).
    """

    def __init__(
        self,
        dsn: str | None = None,
        schema: str = "vector_store",
        pool_size: int = 5,
        dimensions: int = 384,
    ) -> None:
        self._dsn = dsn
        self._schema = schema
        self._pool_size = pool_size
        self._dimensions = dimensions
        self._pool: Any = None

    @property
    def store_name(self) -> str:
        return "pgvector"

    async def _get_pool(self) -> Any:
        """Lazy-initialized asyncpg connection pool."""
        if self._pool is None:
            try:
                import asyncpg
            except ModuleNotFoundError:
                raise RuntimeError("asyncpg is not installed") from None

            self._pool = await asyncpg.create_pool(
                dsn=self._dsn, min_size=1, max_size=self._pool_size
            )
            async with self._pool.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self._schema}")
        return self._pool

    async def health_check(self) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def create_collection(self, name: str, **kwargs: Any) -> bool:
        if await self.collection_exists(name):
            return False
        pool = await self._get_pool()
        dims = kwargs.get("dimensions", self._dimensions)
        async with pool.acquire() as conn:
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._schema}.{name} (
                    id SERIAL PRIMARY KEY,
                    chunk_id TEXT UNIQUE NOT NULL,
                    vector vector({dims}),
                    content TEXT DEFAULT '',
                    report_id TEXT DEFAULT '',
                    version_id TEXT DEFAULT '',
                    embedding_model TEXT DEFAULT '',
                    embedding_provider TEXT DEFAULT '',
                    metadata JSONB DEFAULT '{{}}'::jsonb,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """)
            await conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{name}_chunk_id "
                f"ON {self._schema}.{name} (chunk_id)"
            )
        return True

    async def delete_collection(self, name: str) -> bool:
        if not await self.collection_exists(name):
            return False
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(f"DROP TABLE IF EXISTS {self._schema}.{name}")
        return True

    async def collection_exists(self, name: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT EXISTS (SELECT FROM information_schema.tables "
                    f"WHERE table_schema = '{self._schema}' "
                    f"AND table_name = '{name}')"
                )
                return row[0] if row else False
        except Exception:
            return False

    async def list_collections(self) -> list[str]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT table_name FROM information_schema.tables "
                f"WHERE table_schema = '{self._schema}'"
            )
            return [r[0] for r in rows]

    async def insert(self, collection: str, documents: list[VectorDocument]) -> int:
        pool = await self._get_pool()
        count = 0
        async with pool.acquire() as conn:
            for doc in documents:
                try:
                    await conn.execute(
                        f"""
                        INSERT INTO {self._schema}.{collection}
                            (chunk_id, vector, content, report_id, version_id,
                             embedding_model, embedding_provider, metadata)
                        VALUES ($1, $2::vector, $3, $4, $5, $6, $7, $8::jsonb)
                        ON CONFLICT (chunk_id) DO NOTHING
                        """,
                        doc.chunk_id,
                        doc.vector,
                        doc.text,
                        doc.metadata.report_id,
                        doc.metadata.version_id,
                        doc.metadata.embedding_model,
                        doc.metadata.embedding_provider,
                        json.dumps(doc.metadata.extra, default=str),
                    )
                    count += 1
                except Exception as exc:
                    logger.warning("Insert failed for %s: %s", doc.chunk_id, exc)
        return count

    async def update(self, collection: str, documents: list[VectorDocument]) -> int:
        pool = await self._get_pool()
        count = 0
        async with pool.acquire() as conn:
            for doc in documents:
                try:
                    await conn.execute(
                        f"""
                        UPDATE {self._schema}.{collection}
                        SET vector = $1::vector,
                            content = $2,
                            report_id = $3,
                            version_id = $4,
                            embedding_model = $5,
                            embedding_provider = $6,
                            metadata = $7::jsonb
                        WHERE chunk_id = $8
                        """,
                        doc.vector,
                        doc.text,
                        doc.metadata.report_id,
                        doc.metadata.version_id,
                        doc.metadata.embedding_model,
                        doc.metadata.embedding_provider,
                        json.dumps(doc.metadata.extra, default=str),
                        doc.chunk_id,
                    )
                    count += 1
                except Exception as exc:
                    logger.warning("Update failed for %s: %s", doc.chunk_id, exc)
        return count

    async def delete(
        self,
        collection: str,
        chunk_ids: list[str] | None = None,
        filter: dict[str, Any] | None = None,
    ) -> int:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            if chunk_ids:
                result = await conn.execute(
                    f"DELETE FROM {self._schema}.{collection} " f"WHERE chunk_id = ANY($1::text[])",
                    chunk_ids,
                )
                return _parse_count(result)
            if filter:
                clauses = []
                args: list[Any] = []
                for k, v in filter.items():
                    clauses.append(f"{k} = ${len(args) + 1}")
                    args.append(v)
                where = " AND ".join(clauses)
                result = await conn.execute(
                    f"DELETE FROM {self._schema}.{collection} WHERE {where}",
                    *args,
                )
                return _parse_count(result)
        return 0

    async def count(self, collection: str) -> int:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchval(f"SELECT COUNT(*) FROM {self._schema}.{collection}")
            return row or 0

    async def query(
        self,
        collection: str,
        embedding: list[float],
        top_k: int = 10,
    ) -> list[VectorHit]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT chunk_id, content, metadata, report_id, version_id,
                       embedding_model, embedding_provider,
                       1 / (1 + (vector <=> $1::vector)) AS score
                FROM {self._schema}.{collection}
                ORDER BY vector <=> $1::vector
                LIMIT $2
                """,
                embedding,
                top_k,
            )
        hits: list[VectorHit] = []
        for row in rows:
            meta = {"report_id": row["report_id"], "version_id": row["version_id"],
                    "embedding_model": row["embedding_model"],
                    "embedding_provider": row["embedding_provider"]}
            meta.update(row["metadata"] or {})
            hits.append(
                VectorHit(
                    chunk_id=row["chunk_id"],
                    content=row["content"] or "",
                    metadata=meta,
                    score=float(row["score"]),
                )
            )
        return hits

    async def fetch_all(self, collection: str) -> list[VectorHit]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"SELECT chunk_id, content, metadata FROM {self._schema}.{collection}"
            )
        return [
            VectorHit(
                chunk_id=row["chunk_id"],
                content=row["content"] or "",
                metadata=row["metadata"] or {},
            )
            for row in rows
        ]

    async def delete_by_report(self, collection: str, report_id: str) -> DeleteResult:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                result = await conn.execute(
                    f"DELETE FROM {self._schema}.{collection} " f"WHERE report_id = $1",
                    report_id,
                )
                count = _parse_count(result)
                return DeleteResult(collection_name=collection, deleted_count=count)
        except Exception as exc:
            return DeleteResult(
                collection_name=collection,
                successful=False,
                errors=[str(exc)],
            )

    async def delete_by_version(self, collection: str, version_id: str) -> DeleteResult:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                result = await conn.execute(
                    f"DELETE FROM {self._schema}.{collection} " f"WHERE version_id = $1",
                    version_id,
                )
                count = _parse_count(result)
                return DeleteResult(collection_name=collection, deleted_count=count)
        except Exception as exc:
            return DeleteResult(
                collection_name=collection,
                successful=False,
                errors=[str(exc)],
            )

    def configure(self, params: dict[str, Any]) -> None:
        if "dsn" in params:
            self._dsn = params["dsn"]
            self._pool = None
        if "schema" in params:
            self._schema = params["schema"]
        if "pool_size" in params:
            self._pool_size = params["pool_size"]
        if "dimensions" in params:
            self._dimensions = params["dimensions"]


def _parse_count(result: str) -> int:
    """Parse the 'DELETE N' string returned by asyncpg."""
    try:
        return int(result.split()[-1])
    except (ValueError, IndexError):
        return 0
