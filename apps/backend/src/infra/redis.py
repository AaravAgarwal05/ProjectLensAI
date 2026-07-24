"""Async Redis client singleton with connection pool and JSON helpers."""

import json
import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

_pool: ConnectionPool | None = None
_redis: aioredis.Redis | None = None


async def _ensure_redis() -> aioredis.Redis:
    """Lazy-init the global Redis client and connection pool."""
    global _pool, _redis  # noqa: PLW0603
    if _redis is not None:
        return _redis

    settings = get_settings()
    _pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        max_connections=20,
    )
    _redis = aioredis.Redis(connection_pool=_pool)
    logger.info("Redis client initialised from %s", settings.REDIS_URL.rsplit("@", 1)[-1])
    return _redis


async def get_redis() -> aioredis.Redis:
    """Return the global Redis client singleton.

    Raises:
        RuntimeError: If the client has not been initialised.
    """
    client = await _ensure_redis()
    if client is None:  # pragma: no cover
        raise RuntimeError("Redis not initialised. Call init_redis() first.")
    return client


async def close_redis() -> None:
    """Disconnect the Redis client and clear the singleton."""
    global _pool, _redis  # noqa: PLW0603
    if _redis is not None:
        await _redis.aclose()
        _redis = None
    if _pool is not None:
        await _pool.aclose()
        _pool = None
    logger.info("Redis client disposed")


async def health_check_redis() -> dict[str, Any]:
    """Check Redis connectivity and return status with latency in ms."""
    try:
        client = await get_redis()
        start = time.monotonic()
        await client.ping()
        latency_ms = int((time.monotonic() - start) * 1000)
        return {"status": "ok", "latency_ms": latency_ms}
    except Exception:  # noqa: BLE001
        return {"status": "error", "latency_ms": 0}


# ---------------------------------------------------------------------------
# JSON serialisation helpers
# ---------------------------------------------------------------------------

async def set_json(key: str, value: Any, expire: int | None = None) -> None:
    """Serialize *value* as JSON and store it at *key*.

    Args:
        key: Redis key.
        value: Any JSON-serialisable object.
        expire: Optional TTL in seconds.
    """
    client = await get_redis()
    payload = json.dumps(value, default=str)
    if expire is not None:
        await client.setex(key, expire, payload)
    else:
        await client.set(key, payload)


async def get_json(key: str) -> Any:
    """Fetch and deserialize JSON stored at *key*.

    Returns ``None`` when the key does not exist.
    """
    client = await get_redis()
    payload = await client.get(key)
    if payload is None:
        return None
    return json.loads(payload)


async def delete_key(key: str) -> int:
    """Delete *key* from Redis. Returns the number of keys removed (0 or 1)."""
    client = await get_redis()
    return await client.delete(key)


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------

@asynccontextmanager
async def redis_session() -> AsyncGenerator[aioredis.Redis, None]:
    """Context manager yielding the Redis client, with auto-cleanup on exit.

    Usage::

        async with redis_session() as r:
            await r.set("foo", "bar")
    """
    client = await get_redis()
    try:
        yield client
    finally:
        pass  # the singleton survives — use close_redis() for shutdown
