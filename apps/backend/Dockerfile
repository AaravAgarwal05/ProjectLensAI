FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg2 / asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first for layer caching
COPY pyproject.toml .
COPY apps/backend/pyproject.toml apps/backend/
COPY packages/shared/pyproject.toml packages/shared/
COPY packages/core/pyproject.toml packages/core/
COPY apps/backend/uv.lock apps/backend/

# Install dependencies
RUN cd apps/backend && uv sync --extra dev

# Copy source code
COPY apps/backend/src/ apps/backend/src/
COPY apps/backend/alembic/ apps/backend/alembic/
COPY packages/shared/src/ packages/shared/src/
COPY packages/core/src/ packages/core/src/

EXPOSE 8000

CMD ["uv", "run", "--project", "apps/backend", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
