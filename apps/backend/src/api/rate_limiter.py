"""Rate limiting configuration using slowapi."""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from src.config.settings import get_settings

settings = get_settings()
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)

__all__ = ["limiter", "_rate_limit_exceeded_handler", "SlowAPIMiddleware"]
