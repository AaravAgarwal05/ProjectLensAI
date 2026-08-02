# ProjectLens AI — Documentation

Production-style documentation for the ProjectLens AI RAG platform: a Next.js frontend, a
FastAPI RAG backend, and the infra that runs them. Every page is written from the actual code
and links to the pages it depends on.

---

## Quick start (2 commands)

```bash
# Dev: infra in Docker, apps native with hot-reload
./scripts/dev.sh

# Prod: everything in Docker behind nginx
cp config/.env.production.example .env.production   # fill real secrets (see run-production.md)
./scripts/deploy.sh
```

Full walkthroughs: [Development Run Guide](development/run-dev.md) ·
[Production Run Guide](deployment/run-production.md).

---

## Documentation map

### 1. Understand the system

| Page | Covers |
|------|--------|
| [**Architecture Overview**](architecture/overview.md) | Layered architecture, repo layout, key flows, design decisions |
| [**AI Pipeline**](architecture/ai-pipeline.md) | Ingest (upload→index) + query (chat) pipelines, provider matrix, tracing/eval |
| [**UI/UX Flows**](architecture/ui-ux-flow.md) | User journeys end-to-end: auth, upload, library, collections, chat, settings |
| [**Backend Services**](backend/services.md) | Every service/module in `apps/backend/src/`, startup sequence, dead code |
| [**Plugin Registry Pattern**](architecture/plugin-registry.md) | Why providers plug in behind registries |

### 2. Reference (authoritative, from code)

| Page | Covers |
|------|--------|
| [**API Reference**](api/overview.md) | Every endpoint, auth, error format, rate limits, middleware |
| [**Database Overview**](database/overview.md) | Every table, the Alembic migration chain, known gaps |
| [**Environment Variables**](reference/environment.md) | Every env var, dev + prod values, `.env` templates |
| [**Scripts & Tooling**](reference/scripts.md) | Every script, Makefile target, uv/npm cheatsheet |

### 3. Frontend

| Page | Covers |
|------|--------|
| [**Frontend Architecture**](frontend/architecture.md) | Components, data layer (`src/services/`), state, theming, known debt |
| [**Frontend Pages**](frontend/pages.md) | Every route, what it renders, access level, UI/UX flows |

### 4. Run & deploy

| Page | Covers |
|------|--------|
| [**Development Run Guide**](development/run-dev.md) | Prerequisites, `dev.sh`, manual steps, smoke test, troubleshooting |
| [**Production Run Guide**](deployment/run-production.md) | Deploy, TLS, security checklist, backups, monitoring |
| [**Deployment Overview**](deployment/overview.md) | Dev vs prod compose, cloud-split topology, env file flow |

### 5. Quality

| Page | Covers |
|------|--------|
| [**Testing Overview**](testing/overview.md) | What's tested (~796 tests), how to run, mocking patterns, coverage gaps |
| [**Coding Standards**](development/coding-standards.md) | Python/TS conventions, linting, validation rules |
| [**Getting Started**](development/getting-started.md) | 5-minute manual setup |

---

## Suggested reading order

New to the repo → start here:

```
1. architecture/overview.md        # mental model
2. architecture/ai-pipeline.md     # the core RAG flow
3. api/overview.md                 # what the frontend calls
4. backend/services.md             # where the logic lives
5. reference/environment.md        # before touching .env files
6. development/run-dev.md          # get it running
```

Answering "why is X slow / broken / missing?" →

```
backend/services.md → architecture/ai-pipeline.md → database/overview.md → api/overview.md
        (tracing + eval_runs in ai-pipeline.md explain latency/quality attribution)
```

---

## Env templates (never commit real secrets)

| Template | Copy to | Consumed by |
|----------|---------|-------------|
| `config/.env.production.example` | `.env.production` | `docker-compose.prod.yml`, `scripts/deploy.sh`, `scripts/backup.sh` |
| `config/.env.local.example` | `.env.local` (root) | `docker-compose.yml` (dev infra) |
| `apps/backend/.env.example` | `apps/backend/.env.local` | native backend (pydantic-settings) |
| `apps/frontend/.env.example` | `apps/frontend/.env.local` | Next.js `NEXT_PUBLIC_*` build-time vars |

`.env*` files are gitignored. See [Environment Variables](reference/environment.md) and
[Deployment Overview](deployment/overview.md#environment-file-flow).

---

## Known limitations (honest flags, safe to leave)

- **Stored prefs vs new default** — users registered before 2026-08-02 keep their stored
  `embedding_provider` (was `ollama`); the default is now `gemini`. They can update in Settings.
  See [database/overview.md#users](database/overview.md).
- **Inert leftovers** — `ai_core/chat/database.py::create_tables()` (never called) and the
  `documents.py` / `analysis.py` 501 stubs. See
  [backend/services.md#removed--scaffolding-code](backend/services.md) and
  [api/overview.md#placeholders](api/overview.md).
