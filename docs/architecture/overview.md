# Architecture Overview

ProjectLens AI is a monorepo: a FastAPI RAG backend, a Next.js frontend, and two small shared
packages. Tenancy is **row-level ownership isolation** (`owner_id` scoping) — no per-tenant
schema or database.

```
┌────────────────────────────────────────────────────────────┐
│  FRONTEND — Next.js 16 App Router (apps/frontend)          │
│  React 19 · TS strict · Tailwind + Material-3 tokens       │
│  src/app (routes) · src/services (API mappers) · zustand   │
└───────────────┬────────────────────────────────────────────┘
                │ HTTP/JSON · HttpOnly cookie auth · credentials:'include'
┌───────────────▼────────────────────────────────────────────┐
│  BACKEND — FastAPI (apps/backend)                          │
│                                                            │
│  api/v1/*    routers (thin) + get_current_user guard       │
│  services/   ReportService · ProcessingService ·           │
│              RAGChatService · CollectionService            │
│  ai_core/    chat orchestrator · retrieval · context ·     │
│              llm · chunking · embedding · tracing · eval   │
│  document_processing  parse → clean → metadata             │
│  repository/ generic CRUD · storage/ providers             │
│  database/   SQLAlchemy 2.0 async + Alembic                │
└───────┬──────────────────────┬──────────────────────┬──────┘
        │                      │                      │
   ┌────▼────┐           ┌─────▼─────┐         ┌──────▼──────┐
   │PostgreSQL│           │  ChromaDB │         │    Redis    │
   │ 16       │           │  vectors  │         │ cache/state │
   │ (alembic)│           │ (port 8001)│        │ (port 6379) │
   └─────────┘           └───────────┘         └─────────────┘

   External AI providers: opencode_zen (default LLM) · Google Gemini (LLM + embeddings)
                          Ollama (local LLM + embeddings) · optional Supabase storage
```

---

## Repo layout

| Path | What it is |
|------|-----------|
| `apps/backend/` | FastAPI service. uvicorn on `:8000`. `PYTHONPATH` includes `packages/*` |
| `apps/frontend/` | Next.js 16 App Router. dev `:3000` |
| `packages/shared/` | domain models / DTOs / constants (`ParsedDocument`, report types) |
| `packages/core/` | config, events, registry, utils |
| `scripts/` | dev tooling: `setup.sh`, `dev.sh`, `deploy.sh`, `backup.sh`, `eval_rag.py`, `process_report.py` |
| `docker/` | Dockerfiles (in each app), postgres init, nginx config |
| `docs/` | this documentation suite |

---

## Layer responsibilities

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **API** | `src/api/v1/` | route registration, request validation, auth guard, rate limiting, middleware. Thin — no business logic |
| **Services** | `src/services/` | orchestrate business operations (upload, background processing, RAG answer, collections) |
| **AI core** | `src/ai_core/` | provider-agnostic RAG engine: chat orchestrator, retrieval, context assembly, LLM, chunking, embedding, vector store, tracing, eval |
| **Document processing** | `src/document_processing/` | parse / clean / metadata for uploads |
| **Repository** | `src/repository/` | generic + per-table async data access |
| **Storage** | `src/storage/` | `StorageProvider` (local or Supabase) for uploaded files |
| **Database** | `src/database/` | engine, session factory, models; Alembic owns schema |
| **Infra** | `src/config/`, `src/infra/`, `src/core/` | settings, logging, Redis singleton, bootstrap wiring |

Every layer above storage depends on abstract interfaces (pipeline + registry/factory), not
concrete providers — see [AI Pipeline](ai-pipeline.md) and
[Backend Services](../backend/services.md).

---

## Key flows

| Flow | Path | Detail |
|------|------|--------|
| **Upload → ready** | `POST /reports` → `ProcessingService.process_report` (background) | parse → clean → metadata → chunk → embed → index Chroma → status `ready` |
| **Chat** | `POST /chat/send[/stream]` → `ChatOrchestrator` | rewrite → retrieve → context → prompt → LLM → citations → save → trace |
| **Auth** | `POST /auth/register\|login` sets HttpOnly cookie; every authed call `Depends(get_current_user)` | JWT HS256, 60-min expiry, `token_version` revocation |
| **Search** | `POST /reports/{id}/search` | direct Chroma vector search over one report's chunks |
| **Eval** | `scripts/eval_rag.py` → `POST /eval/runs` | LLM-judge scoring, persisted run + config snapshot |

---

## Design decisions

| Decision | Rationale |
|----------|-----------|
| **Provider registry + factory** (`build_*`) | swap Gemini / Ollama / opencode_zen with zero consumer changes; `fallback` provider gives resilience |
| **Background processing** | upload returns `201` immediately; heavy parse/embed work is async — UI shows status via tabs |
| **Row-level tenancy** | every query scoped by `owner_id`; cross-owner reads → `404` (never `403`) to avoid leaking existence |
| **HttpOnly cookie auth** | no token in JS, XSS-safe; `token_version` bump revokes all outstanding JWTs on logout |
| **Alembic-only schema** | no `create_all` at runtime; migrations run in `entrypoint.sh` before uvicorn |
| **Async-first** | SQLAlchemy async, asyncpg, httpx AsyncClient — high throughput on IO-bound AI calls |
| **Graceful degradation** | bootstrap wraps each dependency (DB/Redis/Chroma/embedding) so one outage doesn't kill startup; health endpoint reports degraded status |
| **Observability built in** | `request_traces` per chat turn + persisted `eval_runs` make quality/latency attributable to `prompt_version` / model / retrieval config |

---

## Detailed guides

| Guide | Contents |
|-------|----------|
| [AI Pipeline](ai-pipeline.md) | ingest + query pipelines, provider matrix, tracing/eval |
| [Backend Services](../backend/services.md) | every service/module in `src/`, startup sequence, dead code |
| [Frontend Architecture](../frontend/architecture.md) | components, data layer, state, theming |
| [Frontend Pages](../frontend/pages.md) | every route + UI/UX flows |
| [API Reference](../api/overview.md) | all endpoints, auth, rate limits, middleware |
| [Database](../database/overview.md) | tables, migration chain, known gaps |
| [UI/UX Flow](ui-ux-flow.md) | user journeys end-to-end |
| [Deployment](../deployment/overview.md) | compose stacks, topologies, env flow |
| [Environment Variables](../reference/environment.md) | every env var, dev + prod values |
| [Scripts & Tooling](../reference/scripts.md) | every script + Makefile target |
| [Testing](../testing/overview.md) | what's tested, how to run, coverage gaps |
