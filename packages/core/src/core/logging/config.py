"""Logging configuration model."""

from pydantic import BaseModel, Field


class LoggingConfig(BaseModel):
    """Configuration for structured logging."""

    level: str = Field(default="INFO", description="Logging level (e.g. DEBUG, INFO, WARNING, ERROR)")
    format: str = Field(
        default="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        description="Log format string",
    )
    output: str = Field(default="console", description="Output target: 'console' or 'json'")
    file_path: str | None = Field(default=None, description="Optional file path for log output")
