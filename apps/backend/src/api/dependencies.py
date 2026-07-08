"""FastAPI dependency injection functions."""

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import async_session_factory

_security_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session to route handlers.

    The session is automatically closed when the request finishes.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security_scheme),
) -> dict:
    """Resolve the current user from the JWT bearer token.

    This is a placeholder — full implementation will follow.

    Raises:
        HTTPException 401: No or invalid token.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    # TODO: decode JWT and load user from database
    return {"sub": "placeholder-user-id", "role": "user"}
