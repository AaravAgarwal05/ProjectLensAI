#!/usr/bin/env bash
# Container entrypoint: run pending migrations, then start the API.
set -euo pipefail

cd /app/apps/backend

echo "→ Running database migrations (alembic upgrade head)..."
/app/.venv/bin/alembic upgrade head
echo "→ Migrations applied."

echo "→ Starting uvicorn..."
exec /app/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
