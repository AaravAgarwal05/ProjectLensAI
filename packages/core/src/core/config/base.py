"""Base configuration model."""

from typing import Self

from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    """Base configuration loaded from environment variables and .env files.

    Subclass this to define typed configuration models for different
    components.  Settings are automatically populated from environment
    variables (prefixed by ``env_prefix``) and ``.env`` files.
    """

    model_config = {
        "env_prefix": "PL_",
        "env_file": ".env",
        "extra": "ignore",
    }

    def to_dict(self) -> dict:
        """Return configuration as a plain dictionary."""
        return self.model_dump()

    def merge(self, other: dict) -> Self:
        """Return a new instance with values from *other* overriding current ones."""
        merged = self.model_copy(update=other)
        return merged
