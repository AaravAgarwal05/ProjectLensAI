# Development Run Guide

> **Last updated:** 2026-07-08
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
1. Creates `.env.local` from `.env.local.example` if missing
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

### 2. Environment Variables

```bash
cp .env.local.example .env.local
```

Key dev defaults (from `.env.local`):
| Variable | Default | Notes |
|----------|---------|-------|
| `APP_ENV` | `development` | Enables debug endpoints |
| `DEBUG` | `true` | Full stack traces |
| `STORAGE_PROVIDER` | `local` | Files stored on disk |

### 3. Start Infrastructure (Docker)

```bash
docker compose -f docker-compose.dev.yml up -d
```

This starts three containers:

| Service | Port | Health Check | Persistence |
|---------|------|-------------|-------------|
| PostgreSQL 16 + pgvector | `5432` | `pg_isready` | `postgres_data` volume |
| ChromaDB | `8001` | `GET /api/v1/heartbeat` | `chroma_data` volume |
| Redis 7 + AOF | `6379` | `redis-cli ping` | `redis_data` volume |

Check status:
```bash
docker compose -f docker-compose.dev.yml ps
```

View logs:
```bash
./scripts/logs.sh         # all services
./scripts/logs.sh postgres  # single service
```

### 4. Install Backend Dependencies

```bash
cd apps/backend
pip install -e ".[dev]"
cd ../..
```

### 5. Run Database Migrations

```bash
cd apps/backend
alembic upgrade head
cd ../..
```

### 6. Start Backend Server

```bash
cd apps/backend
PYTHONPATH=. uvicorn main:app --reload --host 0.0.0.0 --port 8000
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

# Expected response:
# {"status":"healthy","version":"0.1.0"}
```

### Run Tests

```bash
./scripts/test.sh
```

### Check Database Connection

```bash
docker compose -f docker-compose.dev.yml exec postgres psql -U postgres -d projectlens -c "\dt"
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
docker compose -f docker-compose.dev.yml ps
docker compose -f docker-compose.dev.yml top
```

---

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 5432
sudo lsof -i :5432
# Kill the process or change the port mapping in docker-compose.dev.yml
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
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d
cd apps/backend
alembic upgrade head
```

### Python Import Errors

Ensure all packages are installed in editable mode:
```bash
pip install -e apps/backend
pip install -e packages/core
pip install -e packages/shared
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
