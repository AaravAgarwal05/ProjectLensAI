"""TraceStore — persists request traces to the database.

Uses its own ``async_session_factory`` session so recording a trace is
independent of the request's DB session (which commits at request end).
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.ai_core.tracing.database import RequestTraceModel
from src.ai_core.tracing.models import RequestTrace
from src.database import session as db_session


def _session_factory() -> async_sessionmaker[AsyncSession] | None:
    """Return the global session factory, reading it live so ``init_db()``
    (which runs after import) is reflected here."""
    return db_session.async_session_factory

logger = logging.getLogger(__name__)


class TraceStore:
    """Persistence for request traces."""

    @staticmethod
    async def record(trace: RequestTrace) -> None:
        """Insert a trace row. Failures are logged, never raised."""
        factory = _session_factory()
        if factory is None:
            logger.warning("TraceStore: DB not initialised, skipping trace record")
            return
        try:
            data = trace.to_dict()
            async with factory() as session:
                session.add(
                    RequestTraceModel(
                        request_id=data["request_id"],
                        user_id=data.get("user_id") or None,
                        session_id=data.get("session_id") or None,
                        prompt_version=data.get("prompt_version") or None,
                        prompt_hash=data.get("prompt_hash") or None,
                        model=data.get("model") or None,
                        provider=data.get("provider") or None,
                        cache_hit=bool(data.get("cache_hit")),
                        stages=data.get("stages", {}),
                        counts=data.get("counts", {}),
                    )
                )
                await session.commit()
        except Exception:
            logger.exception("TraceStore: failed to record trace")

    @staticmethod
    async def recent(limit: int = 50) -> list[dict]:
        """Return the most recent traces (newest first)."""
        factory = _session_factory()
        if factory is None:
            return []
        async with factory() as session:
            result = await session.execute(
                select(RequestTraceModel)
                .order_by(RequestTraceModel.created_at.desc())
                .limit(limit)
            )
            rows = result.scalars().all()
        out: list[dict] = []
        for r in rows:
            out.append(
                {
                    "id": r.id,
                    "request_id": r.request_id,
                    "user_id": r.user_id,
                    "session_id": r.session_id,
                    "prompt_version": r.prompt_version,
                    "prompt_hash": r.prompt_hash,
                    "model": r.model,
                    "provider": r.provider,
                    "cache_hit": r.cache_hit,
                    "stages": r.stages or {},
                    "counts": r.counts or {},
                    "created_at": (
                        r.created_at.isoformat() if r.created_at else None
                    ),
                }
            )
        return out
