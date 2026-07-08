"""System-wide limits and configuration defaults."""

# Maximum allowed file upload size in bytes (100 MB).
MAX_FILE_SIZE: int = 100 * 1024 * 1024

# Maximum number of characters per document chunk.
MAX_CHUNK_SIZE: int = 1000

# Minimum number of characters per document chunk.
MIN_CHUNK_SIZE: int = 100

# Maximum number of concurrent background processing jobs.
MAX_CONCURRENT_JOBS: int = 10

# Default page size for paginated list endpoints.
DEFAULT_PAGE_SIZE: int = 20

# Maximum allowed page size for paginated list endpoints.
MAX_PAGE_SIZE: int = 100

# JWT access token expiration time in minutes.
JWT_EXPIRATION_MINUTES: int = 60

# Maximum number of API requests allowed per minute per user.
RATE_LIMIT_PER_MINUTE: int = 60
