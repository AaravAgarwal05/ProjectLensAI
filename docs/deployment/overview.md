# Deployment Overview

How the system is deployed, both environments, and the two compose files.

---

## Guides

| Guide | Covers |
|-------|--------|
| [Development Run Guide](../development/run-dev.md) | Local dev: infra in Docker, app native |
| [Production Run Guide](run-production.md) | Full production stack behind Nginx |
| [Environment Variables](../reference/environment.md) | Every env var, dev + prod values |
| [Scripts & Tooling](../reference/scripts.md) | `scripts/*.sh`, `Makefile`, `eval_rag.py` |

---

## Two compose files

| File | For | Includes |
|------|-----|----------|
| `docker-compose.yml` | Local dev (or "everything in Docker") | postgres, chroma, redis, backend, frontend |
| `docker-compose.prod.yml` | Production | postgres, chroma, redis, backend, frontend, nginx |

### Dev compose (`docker-compose.yml`)

- **postgres** `pgvector/pgvector:pg16` — port `5432`, init scripts from `docker/postgres/init`
- **chroma** `chromadb/chroma:latest` — host port `8001` → container `8000`, persistent volume
- **redis** `redis:7-alpine` — port `6379`, AOF enabled
- **backend** built from `apps/backend/Dockerfile` — port `8000`; env pointed at the in-network
  service names (`postgres`, `redis`, `chroma`); `OLLAMA_HOST` defaults to `host.docker.internal`
- **frontend** built from `apps/frontend/Dockerfile` — port `3000`; `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`

Health gates: backend `depends_on` each infra service **healthy** before starting.

### Prod compose (`docker-compose.prod.yml`)

Differences from dev:

- **Secrets required** — `POSTGRES_USER`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `SECRET_KEY` have
  **no defaults** (`${VAR:?...}`), read from `.env.production` (also loaded via `env_file`)
- **Redis** runs with a requirepass and a `512mb` maxmemory LRU policy
- **Resource limits** on postgres (1G/1CPU), chroma (1G/0.5CPU), redis (512M/0.5CPU), backend (1G/1CPU)
- **nginx** `nginx:1.31.3-alpine` on port `80`, config from `docker/nginx/default.conf` —
  reverse-proxies `/api/` → backend, everything else → frontend; adds hardening headers
- Frontend `NEXT_PUBLIC_API_URL=/api/v1` (same-origin via nginx)

---

## Deployment topologies

### 1. Single-server Docker Compose (this repo's default)

```
Internet ── :80 ──▶ nginx ──┬─▶ /api/* ──▶ backend:8000 ──▶ postgres / redis / chroma
                            └─▶ *      ──▶ frontend:3000
```
`scripts/deploy.sh` builds, starts, and health-checks this stack. See
[Production Run Guide](run-production.md).

### 2. Managed cloud split (recommended for production traffic)

The app is cloud-native; components can be hosted by managed services:

| Component | This repo (self-hosted) | Managed alternative |
|-----------|------------------------|---------------------|
| PostgreSQL | `pgvector/pgvector:pg16` | Neon / Supabase / Railway Postgres (pgvector supported) |
| ChromaDB | `chromadb/chroma` | Managed vector DB (or keep self-hosted Chroma) |
| Redis | `redis:7-alpine` | Upstash Redis |
| Backend | FastAPI Docker image | Railway / Render (build from `apps/backend/Dockerfile`) |
| Frontend | Next.js Docker image | Vercel (`apps/frontend`) |
| File storage | Local / Supabase | Supabase storage buckets |

For the split topology set the same env vars (see
[Environment Variables](../reference/environment.md)) pointing at the external services and
deploy frontend/backend separately.

---

## Environment file flow

| File | Consumer |
|------|----------|
| `apps/backend/.env.local` | Native backend (pydantic-settings), `scripts/dev.sh` |
| root `.env.local` | `docker-compose.yml` (dev) |
| `.env.production` | `docker-compose.prod.yml` + `scripts/deploy.sh` + `scripts/backup.sh` |
| `apps/frontend/.env.local` | Next.js `NEXT_PUBLIC_*` build-time vars |

---

## Keepalive / free-tier notes

If the backend runs on a free host that idles, hit the health endpoint periodically to keep it
warm (e.g. UptimeRobot pinging `GET /api/v1/health` every ~10 min). The health route performs a
Redis `ping` — the internal `/ping` equivalent keeps the dependency hot too. See
[API Overview](../api/overview.md#health) for the endpoints.
