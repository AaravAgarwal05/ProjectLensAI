"""Authentication endpoints (register, login, token refresh, profile).

All endpoints persist to the database using real password hashing and JWT tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, get_db
from src.database.models import User

router = APIRouter()

# ──────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    created_at: str

    @classmethod
    def from_orm(cls, user: User) -> "UserOut":
        return cls(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
            created_at=str(user.created_at),
        )


class AuthResponse(BaseModel):
    user: UserOut
    token: str


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt via the bcrypt library directly."""
    import bcrypt as _bcrypt

    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    import bcrypt as _bcrypt

    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_token(user_id: str) -> str:
    """Create a signed JWT access token."""
    import time

    from jose import jwt

    from src.config.settings import get_settings

    settings = get_settings()
    payload = {
        "sub": user_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + settings.JWT_EXPIRATION_MINUTES * 60,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────


@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    """Register a new user account.

    Validates uniqueness, hashes the password, inserts into DB,
    and returns a JWT token + user profile.
    """
    # Validate inputs
    if not body.email or "@" not in body.email:
        raise HTTPException(status_code=422, detail="Invalid email address")
    if len(body.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    if len(body.name.strip()) < 2:
        raise HTTPException(status_code=422, detail="Name must be at least 2 characters")

    # Check existing user
    result = await db.execute(select(User).where(User.email == body.email.strip().lower()))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    # Create user
    user = User(
        email=body.email.strip().lower(),
        name=body.name.strip(),
        hashed_password=_hash_password(body.password),
        role="user",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token = _create_token(str(user.id))
    return AuthResponse(user=UserOut.from_orm(user), token=token)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    """Authenticate a user and return a JWT access token."""
    result = await db.execute(
        select(User).where(User.email == body.email.strip().lower())
    )
    user = result.scalar_one_or_none()
    if not user or not _verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _create_token(str(user.id))
    return AuthResponse(user=UserOut.from_orm(user), token=token)


@router.get("/me", response_model=UserOut)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserOut:
    """Return the currently authenticated user's profile."""
    return UserOut.from_orm(current_user)


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    current_user: User = Depends(get_current_user),
) -> AuthResponse:
    """Issue a new JWT for the currently authenticated user."""
    token = _create_token(str(current_user.id))
    return AuthResponse(user=UserOut.from_orm(current_user), token=token)


@router.post("/logout")
async def logout() -> dict:
    """Logout — no-op for stateless JWT auth.

    Clients should discard the token on their end.
    """
    return {"message": "Logged out successfully"}
