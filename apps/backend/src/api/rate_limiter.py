"""Rate limiting configuration using slowapi."""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379/0")

__all__ = ["limiter", "_rate_limit_exceeded_handler", "SlowAPIMiddleware"]
