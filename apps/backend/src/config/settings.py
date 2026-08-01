"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application settings loaded from .env file or environment variables."""

    # Project metadata
    PROJECT_NAME: str = "ProjectLens AI"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
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

    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000

    # Google AI Studio (primary LLM provider)
    GOOGLE_API_KEY: str = ""

    # Ollama (secondary LLM provider)
    OLLAMA_HOST: str = "localhost"
    OLLAMA_PORT: int = 11434

    # OpenCode Zen (free-model LLM provider — set OPENCODE_ZEN_API_KEY to use)
    OPENCODE_ZEN_API_KEY: str = ""

    @property
    def ollama_base_url(self) -> str:
        return f"http://{self.OLLAMA_HOST}:{self.OLLAMA_PORT}"

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=[".env.local", ".env"],
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def _fail_fast_on_insecure_secret_key(self) -> "AppSettings":
        """Refuse to boot with the shipped insecure SECRET_KEY default.

        The hardcoded default is public in the repository — signing JWTs with it
        would let anyone forge tokens. Require an explicit override.
        """
        if self.SECRET_KEY == "change-this-in-production":
            raise ValueError(
                "SECRET_KEY is set to the known-insecure default. "
                "Generate a strong random key (e.g. `openssl rand -hex 64`) and "
                "set it via SECRET_KEY in the environment or .env before booting."
            )
        return self


@lru_cache
def get_settings() -> AppSettings:
    """Return a cached singleton of the application settings."""
    return AppSettings()
