# Development Run Guide

> **Last updated:** 2026-07-27
> **Target:** Local development machine

---

## Overview

This guide covers running ProjectLens AI in development mode. The dev environment uses Docker for infrastructure services (PostgreSQL, ChromaDB, Redis) and runs backend/frontend natively for hot-reload.

---

## Quick Start (One Command)

```bash
./scripts/dev.sh
```

This single command:
1. Creates `.env.local` from `config/.env.local.example` if missing
2. Starts PostgreSQL, ChromaDB, Redis via Docker Compose
3. Waits for each service health check to pass
4. Runs Alembic database migrations
5. Launches backend (uvicorn with hot-reload)
6. Launches frontend (Next.js dev server)

---

## Manual Step-by-Step

### 1. Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.12+ | `python --version` |
| Node.js | 20+ | `node --version` |
| npm | 10+ | `npm --version` |
| Docker | 24+ | `docker --version` |
| Docker Compose | v2 | `docker compose version` |
| uv | latest | `uv --version` |

Install uv if missing:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Environment Variables

`./scripts/dev.sh` handles this automatically. Manually:

```bash
# Backend env (read by pydantic-settings when running natively)
cp apps/backend/.env.example apps/backend/.env.local

# Root .env.local (used by docker-compose.yml for the infra services)
cp config/.env.local.example .env.local
```

Key dev defaults (from `apps/backend/.env.local`):
| Variable | Default | Notes |
|----------|---------|-------|
| `APP_ENV` | `development` | Enables debug endpoints |
| `DEBUG` | `true` | Full stack traces |
| `STORAGE_PROVIDER` | `local` | Files stored on disk |

### 3. Start Infrastructure (Docker)

```bash
docker compose -f docker-compose.yml up -d
```

This starts three containers:

| Service | Port | Health Check | Persistence |
|---------|------|-------------|-------------|
| PostgreSQL 16 + pgvector | `5432` | `pg_isready` | `postgres_data` volume |
| ChromaDB | `8001` | `GET /api/v1/heartbeat` | `chroma_data` volume |
| Redis 7 + AOF | `6379` | `redis-cli ping` | `redis_data` volume |

Check status:
```bash
docker compose -f docker-compose.yml ps
```

View logs:
```bash
./scripts/logs.sh         # all services
./scripts/logs.sh postgres  # single service
```

### 4. Install Backend Dependencies

```bash
cd apps/backend
uv sync --extra dev
cd ../..
```

This installs all Python dependencies including dev tools (pytest, ruff, mypy)
and the local monorepo packages (`projectlens-shared`, `projectlens-core`) as
editable path dependencies.

### 5. Run Database Migrations

```bash
cd apps/backend
uv run alembic upgrade head
cd ../..
```

### 6. Start Backend Server

```bash
cd apps/backend
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at: http://localhost:8000
Interactive docs: http://localhost:8000/docs
Alternative API docs: http://localhost:8000/redoc

### 7. Start Frontend

```bash
cd apps/frontend
npm install
npm run dev
```

The frontend is available at: http://localhost:3000

---

## Verification

### Smoke Test

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Expected response shape:
# {"status":"ok","version":"0.1.0","uptime":...,"dependencies":{...}}
# status is "ok" | "degraded" | "down"
```

### Run Tests

```bash
./scripts/test.sh
```

### Check Database Connection

```bash
docker compose -f docker-compose.yml exec postgres psql -U postgres -d projectlens -c "\dt"
```

---

## Common Operations

### Stop Everything

```bash
./scripts/down.sh              # stop containers
./scripts/down.sh -v           # stop + remove volumes (data loss!)
```

### Full Reset

```bash
./scripts/reset.sh             # confirmation prompt → wipes everything → restarts
```

### View Service Logs

```bash
./scripts/logs.sh              # tail all
./scripts/logs.sh postgres     # tail specific service
```

### Docker Service Health

```bash
docker compose -f docker-compose.yml ps
docker compose -f docker-compose.yml top
```

### Managing Dependencies with uv

```bash
# Add a dependency
cd apps/backend && uv add requests

# Add a dev dependency
cd apps/backend && uv add --dev pytest-asyncio

# Add an optional dependency
cd apps/backend && uv add --extra ai sentence-transformers

# Update all dependencies from lock file
cd apps/backend && uv sync --extra dev

# Run a command in the venv
cd apps/backend && uv run python -c "import chromadb; print('ok')"
```

---

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 5432
sudo lsof -i :5432
# Kill the process or change the port mapping in docker-compose.yml
```

### Docker Permission Denied

Ensure your user is in the `docker` group:
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Alembic Migration Fails

```bash
# Reset the database
docker compose -f docker-compose.yml down -v
docker compose -f docker-compose.yml up -d
cd apps/backend
uv run alembic upgrade head
```

### Python Import Errors

Ensure all packages are installed:
```bash
cd apps/backend && uv sync --extra dev
```

### uv Command Not Found

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Then restart your terminal
```

---

## Architecture Notes

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend  │────▶│   Backend    │────▶│  PostgreSQL  │
│  :3000      │     │  :8000       │     │  :5432       │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │              ┌──────────────┐
                           ├─────────────▶│   ChromaDB   │
                           │              │  :8001       │
                           │              └──────────────┘
                           │              ┌──────────────┐
                           └─────────────▶│    Redis     │
                                          │  :6379       │
                                          └──────────────┘
```

- Backend and frontend run **outside** Docker for hot-reload
- Infrastructure services run **inside** Docker for isolation
- All containers share the `projectlens-network` bridge network
