"""Shared constants, enumerations, and system limits for the ProjectLens platform."""

from shared.constants.events import EventType
from shared.constants.limits import (
    DEFAULT_PAGE_SIZE,
    JWT_EXPIRATION_MINUTES,
    MAX_CHUNK_SIZE,
    MAX_CONCURRENT_JOBS,
    MAX_FILE_SIZE,
    MAX_PAGE_SIZE,
    MIN_CHUNK_SIZE,
    RATE_LIMIT_PER_MINUTE,
)
from shared.constants.roles import UserRole
from shared.constants.status import DocumentStatus, ProcessingStatus

__all__ = [
    "UserRole",
    "DocumentStatus",
    "ProcessingStatus",
    "EventType",
    "MAX_FILE_SIZE",
    "MAX_CHUNK_SIZE",
    "MIN_CHUNK_SIZE",
    "MAX_CONCURRENT_JOBS",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "JWT_EXPIRATION_MINUTES",
    "RATE_LIMIT_PER_MINUTE",
]
