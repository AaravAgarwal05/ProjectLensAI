"""FastAPI security dependencies for authentication and authorisation."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.jwt import decode_token

_security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security_scheme),
) -> dict:
    """Resolve the current user from the JWT bearer token.

    Returns:
        A dict containing user claims (sub, role, etc.).

    Raises:
        HTTPException 401: Missing or invalid token.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        payload = decode_token(credentials.credentials)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    return payload


def require_role(required_role: str):
    """Create a dependency that enforces the user has a specific role.

    Usage::

        @router.get("/admin")
        async def admin_only(user: dict = Depends(require_role("admin"))):
            ...

    Args:
        required_role: The role name the user must possess.

    Returns:
        A FastAPI dependency callable.
    """

    async def _role_checker(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        user_role = current_user.get("role", "user")
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required, but user has '{user_role}'",
            )
        return current_user

    return _role_checker
