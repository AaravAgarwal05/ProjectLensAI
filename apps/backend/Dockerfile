FROM python:3.14-slim

WORKDIR /app

# Install system dependencies for psycopg2 / asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install uv (pinned — :latest moves and busts the dep layer cache)
COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /uvx /bin/

# Copy dependency files first for layer caching
COPY pyproject.toml .
COPY uv.lock .
COPY apps/backend/pyproject.toml apps/backend/
COPY packages/shared/pyproject.toml packages/shared/
COPY packages/core/pyproject.toml packages/core/

# Install dependencies (frozen lock, no dev deps in runtime).
# Deps files are copied above, source below — so BuildKit reuses this layer
# on code-only rebuilds. The cache mount persists downloaded wheels across
# builds, so a pyproject.toml change doesn't re-download the 2.5GB of
# torch/nvidia packages.
WORKDIR /app/apps/backend

RUN --mount=type=cache,target=/root/.cache/uv,id=uv-cache \
    uv sync --frozen --no-dev && \
    ls -la /app/.venv/bin/uvicorn

# Copy source code
WORKDIR /app
COPY apps/backend/src/ apps/backend/src/
COPY apps/backend/alembic/ apps/backend/alembic/
COPY packages/shared/src/ packages/shared/src/
COPY packages/core/src/ packages/core/src/
COPY apps/backend/entrypoint.sh apps/backend/entrypoint.sh

# uv sync ran before source copy, so editable installs are stale. Expose the
# source roots directly — same effect, no `uv run` wrapper layer at runtime.
ENV PYTHONPATH=/app/apps/backend:/app/packages/core/src:/app/packages/shared/src

# Run as an unprivileged user — the process only writes to /tmp (temp
# parse files), which is world-writable.
RUN useradd --create-home --uid 10001 appuser && \
    chmod +x /app/apps/backend/entrypoint.sh
USER appuser

EXPOSE 8000

# The entrypoint runs `alembic upgrade head` before starting the API, so a
# deploy can never boot against an un-migrated database. uvicorn runs
# directly from the workspace venv (no `uv run` layer at runtime).
CMD ["/app/apps/backend/entrypoint.sh"]
