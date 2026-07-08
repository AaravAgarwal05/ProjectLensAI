"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application settings loaded from .env file or environment variables."""

    # Project metadata
    PROJECT_NAME: str = "ProjectLens AI"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENV: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/projectlens"
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    SECRET_KEY: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    # Storage
    STORAGE_PROVIDER: str = "local"
    STORAGE_LOCAL_PATH: str = "./data/storage"

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "reports"
    MAX_UPLOAD_SIZE: int = 104857600
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".docx"]

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Logging
    LOG_LEVEL: str = "DEBUG"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> AppSettings:
    """Return a cached singleton of the application settings."""
    return AppSettings()
