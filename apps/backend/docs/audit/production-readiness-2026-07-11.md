# ProjectLens AI — Production Readiness & Architecture Audit

**Date:** 2026-07-11  
**Auditor:** Principal Staff Engineer (simulated review)  
**Scope:** Full-stack audit across 12 dimensions  
**Codebase:** 16,655 LOC (src/) + 10,202 LOC (tests/) — 269 total source/test files  
**Status: NOT PRODUCTION READY**

---

## Executive Summary

ProjectLens AI has a well-structured core with clean architectural boundaries between its 7 AI modules and a comprehensive test suite at the unit level (273 passing tests). However, the project is **not production-ready**. Critical gaps exist in every dimension required for production deployment: security (no auth implementation, hardcoded secrets), infrastructure (no docker-compose, no CI/CD), operations (no health checks on AI components, no monitoring), and end-to-end validation (no E2E or integration tests). The architecture is sound at the module level but lacks the runtime scaffolding needed for production.

**Verdict:** Blocked. Address Critical and High findings before any production deployment.

---

## 1. Architecture Review

### Strengths

| Aspect | Finding |
|--------|---------|
| Import Hierarchy | Clean, unidirectional: `context ← llm ← chat`. No circular dependencies. Verified by static analysis. |
| Module Isolation | 7 independent AI modules in `src/ai_core/` with clear responsibilities (chunking, embedding, context, llm, retrieval, vector_store, chat) |
| Chat Design | Well-factored: Orchestrator → Manager → Repository layering. Strategy pattern for mode mapping (single/multi/comparison). Clean delegation of retrieval via callable. |
| Streaming | Proper async generator pattern with SSE formatting, cancellation via `asyncio.Event` |
| Citation Engine | Clean extraction + dedup logic with configurable limits |

### Weaknesses

| Issue | Severity | Detail |
|-------|----------|--------|
| No DI container | Medium | Ad-hoc `Depends(get_db)` throughout. No service registration, no lifecycle management. Adding a new dependency requires touching every constructor. |
| Bootstrap is a no-op | **High** | `src/core/bootstrap.py` only calls `init_db()` with silent failure on error. Zero AI component wiring. The app starts "healthy" even if every AI module is broken. |
| Layer violations (3 files) | Medium | `src/document_processing/exceptions.py`, `src/storage/supabase.py`, `src/services/report_service.py` import `ProjectLensError` from `src.api.exceptions` — lower layers depending on API layer. Must move to shared module. |
| Broken imports in 4 routers | **High** | `analysis.py`, `auth.py`, `documents.py`, `reports.py` import `get_settings` from `src.api.dependencies` where it does **not exist** — will raise `ImportError` at runtime on these endpoints. |
| Dead code with broken imports | Medium | `plugin_registry.py` and `workflows/chat.py` reference classes that don't exist (`BaseLLMProvider`, `BaseRetriever`, `BaseEmbeddingProvider`). Will fail if loaded. |
| Business logic in routers | Medium | `reports.py` constructs `ReportService` in 7+ handlers with inline factory functions. `chat.py` builds `SessionManager`/`MessageManager` per-request with hardcoded placeholder logic. |
| Mixed ORM patterns | Low | Chat models use modern `Mapped[]` syntax; Report models use legacy `__allow_unmapped__ = True`. Inconsistent. |
| No application events | Medium | No startup health self-check, no shutdown graceful drain, no warmup of ML models/embeddings |
| Duplicate `get_db` | Low | Defined in both `src/database/session.py` (unused by any router) and `src/api/dependencies.py` (used by routers) — confusing indirection. |
| ai_core type mismatch | Low | `context/builder.py` imports `DocumentChunk` from shared package, but rest of ai_core uses `src.ai_core.chunking.models.Chunk` — incompatible types across modules. |
| ContextFactory indirection | Low | Defined in `registry.py` but re-exported via `factory.py` — unnecessary indirection for consumers. |

**Recommendation:** Implement a proper DI container (or at minimum a service registry) with explicit wiring in a dedicated `create_services()` factory. Move `ProjectLensError` to a shared/common module (e.g., `src/core/exceptions.py`). Fix the 4 broken `get_settings` imports **immediately** — they are silent runtime bombs. Remove or update dead code with broken imports.

---

## 2. End-to-End Validation

### Coverage Map

| Layer | Unit Tests | Integration Tests | E2E Tests |
|-------|-----------|------------------|-----------|
| Chat | 95 ✅ | 0 ❌ | 0 ❌ |
| Context | 103 ✅ | 0 ❌ | 0 ❌ |
| LLM | 75 ✅ | 0 ❌ | 0 ❌ |
| Chunking | 40+ ✅ | 0 ❌ | 0 ❌ |
| Embedding | 40+ ✅ | 0 ❌ | 0 ❌ |
| Retrieval | 40+ ✅ | 0 ❌ | 0 ❌ |
| Vector Store | 25+ ✅ | 0 ❌ | 0 ❌ |
| **API Layer** | 0 ❌ | 0 ❌ | 0 ❌ |
| **Auth** | 0 ❌ | 0 ❌ | 0 ❌ |

### Critical Gaps

1. **Zero integration tests.** Every test mocks the database or LLM. We have never verified that code works against a real PostgreSQL instance or a real Ollama endpoint.
2. **Zero API-layer tests.** Chat endpoints at `src/api/v1/chat.py` have zero tests. The API router has never been exercised via HTTP.
3. **Zero cross-module tests.** Chunks → Embeddings → Vector Store → Retrieval → Context → LLM pipeline has never been tested end-to-end.
4. **29 failing test files** due to SQLite ARRAY type incompatibility with PostgreSQL. The test suite cannot run cleanly.

### Immediate Actions

1. Add docker-compose with PostgreSQL + Ollama for integration testing
2. Write 5 critical E2E tests: upload document → embed → query → chat → receive answer with citations
3. Fix the 29 SQLite-incompatible tests by making Report model tolerate SQLite or skipping those tests with `pytest.mark.postgresql`

---

## 3. Dependency Injection Audit

### Current State

```python
# src/main.py — minimal wiring
async def lifespan(app):
    init_db(settings.DATABASE_URL)  # wraps in try/except, returns None on failure
    yield

# FastAPI endpoints
@router.post("/chat/send")
async def send_message(
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    # Constructs dependencies inline
    session_mgr = SessionManager(db)
    msg_mgr = MessageManager(db)
    # ... every request re-creates everything
```

### Problems

| Issue | Impact |
|-------|--------|
| No formal container | Every endpoint constructs its own dependency graph — error-prone, hard to maintain |
| No singleton management | LLMProvider, VectorStore clients re-created per-request or not at all |
| No lifecycle hooks | Cannot wire startup/shutdown for expensive resources (embedding model, ChromaDB client) |
| Bootstrap failure invisible | `init_db()` swallows exceptions. App reports "ok" at /health with no DB connectivity. |

### Recommendation

```python
# Target pattern — explicit service registry
class Services:
    def __init__(self, settings, db_pool, llm_provider, vector_store, ...):
        ...
    async def verify_health(self) -> dict[str, bool]: ...

async def lifespan(app):
    services = await create_services(settings)
    app.state.services = services
    health = await services.verify_health()
    assert all(health.values()), f"Startup health check failed: {health}"
    yield
    await services.shutdown()
```

---

## 4. Configuration Audit

### Findings

| Config | Status | Risk |
|--------|--------|------|
| `SECRET_KEY` | `"change-this-in-production"` | **CRITICAL** |
| `DEBUG=True` | Default in .env.example | **High** — leaks stack traces in production |
| `CORS_ORIGINS` | Only `localhost:3000` | Medium — blocks production frontend |
| `REDIS_URL` | Configured but **never used** | Low — dead config, misleading |
| `DATABASE_URL` | Hardcoded defaults | Medium — easy to accidentally use dev DB in prod |
| `SUPABASE_URL`/`SUPABASE_KEY` | Empty strings | Medium — dead config if Supabase not used |
| `ALLOWED_EXTENSIONS` | Only `.pdf, .docx` | Low — may need `.txt, .md, .csv` for AI use cases |
| `JWT_EXPIRATION_MINUTES` | 60 minutes | Medium — no refresh token rotation strategy |
| No `.env` validation | Missing required vars cause runtime errors | Medium |

### Recommendation

- Add `pydantic-settings` validation with `AliasChoices` for env-specific overrides
- Implement `.env.{environment}` file switching (dev/staging/prod)
- Remove `REDIS_URL` until Redis is actually used, or document its purpose
- `SECRET_KEY` must come from secrets manager or env-only — never in defaults
- Add startup validation: fail fast if critical config is missing or invalid

---

## 5. Performance Audit

### Known Performance Issues

| Issue | Severity | Detail |
|-------|----------|--------|
| No connection pooling config | Medium | SQLAlchemy default pool might be wrong for async. Pool size, overflow, timeout all at defaults. |
| No Redis caching | Medium | Redis configured but unused. Every query hits PostgreSQL. No query cache, no session cache, no rate-limit counter. |
| No streaming benchmark | Medium | Chat streaming path has `# latency placeholder` — timing is collected but unused. |
| ChromaDB is single-node | Medium | Vector search uses persistent client — no horizontal scaling, no replication. |
| No query optimization | Low | No composite indexes on common query patterns (session_id + created_at, user_id + status). |
| No background task queue | Medium | Long operations (embedding, chunking) block the request thread. No Celery/ARQ/RQ integration. |

### Benchmark Results

No benchmarks exist. Chat benchmark module (`src/ai_core/chat/benchmark.py`) has the structure to collect metrics but has never been run.

### Recommendation

1. Run the ChatBenchmark against a real database + Ollama to establish baseline latency P50/P95/P99
2. Configure explicit SQLAlchemy pool settings for production load
3. Add composite indexes on `(session_id, created_at)` and `(role, session_id)`
4. Investigate Redis caching layer for chat history + context results
5. Instrument with OpenTelemetry before any performance tuning

---

## 6. Scalability Review

### Architecture Limitations

| Constraint | Impact |
|------------|--------|
| Single-process FastAPI | No horizontal scaling. One process handles all traffic. |
| No docker-compose | No standardized multi-service deployment |
| No async task queue | Embedding + chunking + LLM calls block the request thread. Under load, this causes cascading timeouts. |
| ChromaDB single-node | Vector search cannot scale beyond one machine's RAM |
| No stateless design | Session state in local SQLite for tests, PostgreSQL for prod — sticky sessions may be needed |
| No load testing | Unknown throughput ceiling. Unknown max concurrent users. |

### Horizontal Scaling Requirements

| Component | Scale Strategy | Implemented? |
|-----------|---------------|--------------|
| API | Multiple uvicorn workers / k8s replicas | ❌ |
| LLM | Ollama runs as separate service — good | ✅ (partial) |
| Database | Connection pooling + read replicas | ❌ |
| Vector Store | Need Qdrant/PineScale or clustered ChromaDB | ❌ |
| Task Queue | Need Redis + ARQ/Celery for background work | ❌ |

### Recommendation

Add docker-compose.yml with: API server, PostgreSQL, Ollama, Redis. This gives a local production-like environment for integration testing and establishes the scaling foundation.

---

## 7. Reliability Review

### Current Reliability Score: 3/10

| Area | Status | Risk |
|------|--------|------|
| Startup Health Check | `health_check()` returns "ok" even with zero AI components initialized | **Critical** |
| Graceful Degradation | No partial-failure handling. If embeddings go down, chat is completely broken. | High |
| Retry Logic | Zero retry logic in LLM provider, database calls, or external API calls | Medium |
| Circuit Breaker | No circuit breaker pattern anywhere | Medium |
| Timeouts | No explicit timeout configuration on HTTP clients or database queries | **High** |
| Error Format | Consistent JSON error responses via ProjectLensError — good | ✅ |
| Logging | Structured logging via Python logger — minimal context/span IDs | Medium |
| Rate Limiting | No rate limiting on any endpoint | **High** |

### Reliability Anti-Patterns Found

1. **Bootstrap swallows errors.** If DB init fails, `init_db()` logs a warning and returns None. App starts anyway.
2. **No DB connection verification.** `get_db()` yields a session without verifying connectivity. First request after DB restart fails with no recovery.
3. **Chat message length enforced in validation but not at DB level.** `ChatMessageModel.content` is unbounded `Text`. If validation is bypassed, a 10MB message hits the DB without truncation.
4. **No connection retry in HTTP clients.** The Ollama provider (`httpx.AsyncClient`) has no retry or timeout configuration.

### Recommendation

```python
# Target: health check that actually validates
async def verify_health(app_state) -> dict[str, bool]:
    services = app_state.services
    return {
        "database": await services.db.verify_connection(),
        "ollama": await services.llm.ping(),
        "chromadb": services.vector_store.ping(),
        "redis": await services.cache.ping() if services.cache else True,
    }
```

---

## 8. Database Audit

### Schema Quality

| Table | Status | Issue |
|-------|--------|-------|
| `chat_sessions` | ✅ Good | Proper indexes on `id`, `created_at` |
| `chat_messages` | ✅ Good | FK with CASCADE, index on `session_id`, JSON for citations/metadata |
| `reports` | ⚠️ Needs work | ARRAY(Text) for tags — breaks SQLite. Mixed `server_default` styles |
| `report_versions` | ✅ OK | Straightforward versioning |
| `collections` | ✅ OK | Simple unique constraint on name |
| `collection_reports` | ✅ OK | Composite PK, CASCADE deletes |

### Migration Health

| Check | Status |
|-------|--------|
| Alembic migration exists | ✅ One migration (reports + collections) |
| Chat tables have migration | ❌ No migration for chat sessions/messages |
| `alembic current` works | ❌ `alembic/env.py` fails with ModuleNotFoundError — PYTHONPATH not set |
| Down revision works | Unknown — never tested |
| Migration has tests | ❌ |

### 29 Failing Tests Root Cause

```python
# src/database/models/report.py
class Report(Base):
    __allow_unmapped__ = True
    tags: MutableSequence[Optional[str]] = Column(ARRAY(Text))  # ❌ PostgreSQL-only
```

The Report model uses PostgreSQL ARRAY type. When tests run against SQLite (in-memory), this throws `(sqlite3.InterfaceError) Error binding parameter 5 - probably unsupported type`. This affects all 29 tests that touch the Report model.

### Recommendation

- Add migration for chat tables
- Fix `alembic/env.py` to set PYTHONPATH or use relative imports
- Create a `pytest.mark.postgresql` marker for tests requiring PG-specific features
- Consider `JSON` instead of `ARRAY(Text)` for tags to maintain SQLite compatibility
- Add composite indexes: `(session_id, created_at)` for message listing, `(role, session_id)` for role-based queries

---

## 9. Docker Audit

### Dockerfile Analysis

```dockerfile
FROM python:3.12-slim          # ✅ Reasonable base
RUN apt-get install gcc libpq-dev  # ⚠️ 256MB of build deps — use multi-stage
COPY pyproject.toml .          
RUN pip install -e ".[dev]"    # ❌ Installs dev dependencies in production
COPY src/ src/
COPY alembic/ alembic/
EXPOSE 8000
CMD ["uvicorn", "src.main:app", ...]  # ⚠️ No --workers flag
```

### Missing Infrastructure

| Artifact | Status | Priority |
|----------|--------|----------|
| docker-compose.yml | ❌ Missing | **Critical** |
| .dockerignore | ❌ Missing | Medium |
| Healthcheck instruction | ❌ Missing | High |
| Multi-stage build | ❌ Missing | Medium |
| Production entrypoint | ❌ Uses dev server config | High |
| Non-root user | ❌ Runs as root | **Critical** |

### Recommendation

```dockerfile
# Target pattern
FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml .
RUN pip install --no-cache-dir -e "."
RUN pip install --no-cache-dir gunicorn

FROM python:3.12-slim
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src/ src/
COPY alembic/ alembic/
RUN useradd -m appuser && chown -R appuser /app
USER appuser
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## 10. Security Review

### Security Score: 2/10

| Finding | Severity | Status |
|---------|----------|--------|
| **Hardcoded SECRET_KEY** | **CRITICAL** | Default value `"change-this-in-production"` — JWT tokens can be forged by anyone who reads the codebase |
| **Auth endpoints are stubs** | **CRITICAL** | `/auth/register`, `/auth/login`, `/auth/refresh` all return `"not yet implemented"`. No user authentication exists. |
| **Chat endpoints have no auth** | **CRITICAL** | All chat endpoints are publicly accessible. No `Depends(get_current_user)` on any route. |
| **No rate limiting** | High | Chat endpoints can be abused for unlimited LLM calls, causing cost/servers to be overwhelmed |
| **No input sanitization** | Medium | User messages passed directly to LLM with only length validation. No prompt injection guards. |
| **Supabase keys empty** | Medium | SUPABASE_KEY and SUPABASE_SERVICE_KEY default to empty strings. If swapped to production config, will break. |
| **CORS too restrictive** | Low | Only `localhost:3000` — needs production frontend URL |
| **No audit logging** | High | No user action logging. No way to trace who deleted what or when. |
| **No secrets management** | **Critical** | Credentials in .env file, checked into repos, no Vault/secrets manager integration |

### Exploit Scenarios

1. **Token forgery:** Anyone with the codebase can forge JWT tokens using the hardcoded `SECRET_KEY`. All "protected" endpoints are trivially bypassed.
2. **Unlimited LLM usage:** Chat endpoints have no auth, no rate limiting. An attacker can exhaust API quota or run up Ollama compute costs.
3. **Prompt injection:** User messages go directly to the LLM with no sanitization. An attacker can extract system prompts or issue commands to the underlying model.

### Recommendation

1. **Immediately** remove `SECRET_KEY` from defaults — it must be env-only
2. **Blocking**: Implement JWT auth (register/login/refresh) — the schema exists, just needs real implementation
3. **Blocking**: Add `Depends(get_current_user)` to all chat endpoints
4. Add rate limiting via slowapi or middleware
5. Add prompt injection detection (e.g., `lakera` or regex-based guards)
6. Implement audit logging for all user actions

---

## 11. Testing Review

### Coverage Report

| Module | Test Files | Tests Passing | Tests Failing | Coverage Est. |
|--------|-----------|---------------|---------------|---------------|
| Chat | 9 | 95 | 0 | ~85% (statement) |
| Context | 11 | 103 | 0 | ~80% |
| LLM | 8 | 75 | 0 | ~75% |
| Chunking | 10 | 40+ | 0 | ~90% |
| Embedding | 10 | 40+ | 0 | ~70% |
| Retrieval | 10 | 40+ | 0 | ~70% |
| Vector Store | 7 | 25+ | 0 | ~60% |
| **Report Models** | ~17 | 0 | 29 | 0% (broken) |

### Quality Assessment

| Aspect | Rating | Notes |
|--------|--------|-------|
| Unit test depth | ✅ Good | Most modules have comprehensive unit tests with edge cases |
| Mock usage | ⚠️ Moderate | Mocks are appropriate but mean tests don't validate real behavior |
| Fixture design | ✅ Good | Proper use of pytest fixtures, pytest_plugins pattern |
| Test isolation | ✅ Good | In-memory SQLite per test, no shared state |
| Error path coverage | ⚠️ Moderate | Some modules only test happy path |
| Async testing | ✅ Good | Proper use of pytest-asyncio |
| **Integration tests** | ❌ **None** | **Biggest testing gap** |
| **E2E tests** | ❌ **None** | **Cannot validate user workflows** |
| **Performance tests** | ❌ **None** | **No baseline metrics exist** |
| **Mutation testing** | ❌ **None** | **Unknown test quality** |
| **Property-based tests** | ❌ **None** | Limited edge case discovery |
| **29 broken tests** | ❌ **Critical** | Entire report model test suite unusable |

### Recommendation

1. Fix the 29 SQLite-incompatible tests (high priority)
2. Add 5 E2E tests: document upload → embed → query → chat → verify citations
3. Add integration tests with docker-compose (PostgreSQL + Ollama)
4. Run mutation testing (`mutmut` or `pytest-mutagen`) on the chat module
5. Add property-based tests for message validation and citation extraction

---

## 12. Production Readiness Scorecard

| Dimension | Score | Justification |
|-----------|-------|---------------|
| **Architecture** | 7/10 | Clean module structure, good patterns. No DI container, bootstrap is a no-op. |
| **Testing** | 4/10 | Great unit coverage. Zero integration/E2E tests. 29 broken test files. |
| **Security** | 2/10 | No auth. Hardcoded secrets. No rate limiting. No audit logging. |
| **Configuration** | 4/10 | Pydantic settings = good. But SECRET_KEY default is critical. Redis unused. |
| **Performance** | 3/10 | No benchmarks. No caching. No query optimization. No load testing. |
| **Scalability** | 2/10 | Single process. No docker-compose. No task queue. No horizontal scaling. |
| **Reliability** | 3/10 | No health checks. No retry logic. No circuit breakers. Bootstrap swallows errors. |
| **Operations** | 2/10 | No docker-compose. No CI/CD. No monitoring. No structured logging with trace IDs. |

### Overall Score: **3.4/10**

---

## Priority Order for Fixes

### 🔴 Critical (Blocking Production)

| # | Fix | Effort | Impact |
|---|-----|--------|--------|
| 1 | Implement authentication (register/login/JWT) | 3-5 days | Unblocks all auth-gated features. Fixes 3 Critical security issues. |
| 2 | Remove hardcoded SECRET_KEY. Enforce env-only. | 1 hour | Eliminates token forgery vulnerability immediately. |
| 3 | Add auth dependency to all chat/protected endpoints | 1 day | Prevents unauthorized LLM usage. |
| 4 | Add docker-compose.yml (API + PG + Ollama + Redis) | 1 day | Enables E2E testing, standardized dev environment, path to prod. |
| 5 | Fix 29 SQLite-incompatible tests | 1 day | Clean test suite. Developers can trust test results. |

### 🟠 High (Should Block Unless Emergency)

| # | Fix | Effort | Impact |
|---|-----|--------|--------|
| 6 | Fix broken `get_settings` imports in 4 routers (will crash at runtime) | 1 hour | Prevents ImportError on analysis, auth, documents, and reports endpoints. |
| 7 | Move `ProjectLensError` to shared module (`src/core/exceptions.py`) | 1 hour | Eliminates layer violations. |
| 8 | Implement startup health check for all AI components | 1 day | App won't silently start broken. |
| 9 | Write bootstrap service registry / DI container | 2-3 days | Explicit wiring, singleton management, lifecycle hooks. |
| 10 | Add rate limiting to chat endpoints | 1 day | Prevents abuse and runaway costs. |
| 11 | Add 5 critical E2E tests (upload → embed → query → chat → citations) | 2 days | Validates the entire pipeline actually works. |
| 12 | Add connection pooling + retry + timeout config | 1 day | Prevents cascading failures under load. |

### 🟡 Medium (Next Sprint)

| # | Fix | Effort |
|---|-----|--------|
| 11 | Set up Redis caching for chat history / context results | 2 days |
| 12 | Add OpenTelemetry instrumentation | 2-3 days |
| 13 | Implement multi-stage Docker build + .dockerignore | 1 day |
| 14 | Add composite indexes on chat_messages | 1 hour |
| 15 | Add audit logging middleware | 1 day |
| 16 | Run ChatBenchmark against real services for baseline | 1 day |
| 17 | Implement background task queue (ARQ + Redis) for long operations | 3-5 days |

### 🔵 Low (Nice-to-Have)

| # | Fix | Effort |
|---|-----|--------|
| 18 | Add property-based tests | 2 days |
| 19 | Add mutation testing | 1 day |
| 20 | Migration for chat tables in Alembic | 1 day |
| 21 | Switch Report model tags from ARRAY(Text) to JSON | 2 hours |
| 22 | Add prompt injection detection | 2 days |

---

## Detailed Code-Level Findings

### Chat Module (`src/ai_core/chat/`)

`orchestrator.py:118` — `_` assignment collects latency but discards it:
```python
_ = (time.monotonic() - start) * 1000  # latency placeholder
```
Either log it, add to metrics, or remove. Dead code confuses maintainers.

`orchestrator.py:188` — Citation extraction in streaming path fires only on `finish_reason`:
```python
if chunk.finish_reason:
    citations = self._citations.extract(ctx.chunks)
```
The `extract` method already works without response text — this is correct, but the comment implies it needs final text. The non-streaming path passes `response.text` while streaming doesn't. Both work because `extract` tolerates empty text, but this asymmetry should be documented.

`session_manager.py` — All methods use `flush()` not `commit()`. This is correct for test compatibility (rollback works), but means a process crash between operations loses data. Session manager should have a `commit()` method for production use.

`citations.py` — CitationEngine has no unit tests in the 95-chat-test count. Need dedicated citation extraction tests with edge cases (empty chunks, duplicate source_ids, max_citations boundary).

### Context Module (`src/ai_core/context/`)

`ContextAssemblyPipeline.run()` accepts `history: list[Any]` — should accept `list[ChatMessageModel | dict]`. The `# type: ignore[arg-type]` in orchestrator.py signals this.

### LLM Module (`src/ai_core/llm/`)

No retry logic. If Ollama is restarting or overloaded, the request fails immediately. Minimum: 3 retries with exponential backoff.

### API Layer (`src/api/v1/`)

`chat.py` — All 9 endpoints are "working" (pass tests) but use a placeholder response generator. Real LLM orchestration integration is explicitly marked as TODO.

`auth.py` — Three endpoints, all stubs. Auth is the critical path blocker for production.

### Infrastructure

`.env.example` — Contains `SECRET_KEY=change-this-in-production` and `DEBUG=true`. If this file is used as a template for production deployment, the app will ship with a known key and debug mode enabled. This is the single highest-risk finding in this audit.

---

## Conclusion

ProjectLens AI has the structural foundation of a well-designed application. The AI module architecture is clean, the chat pipeline is well-factored, and the unit test coverage is comprehensive at the module level. This is a **strong foundation** that makes the critical gaps fixable without architectural rewrites.

However, the project is currently at the "demo/MVP" stage, not "production." The gaps between the current state and production-ready are in infrastructure and security scaffolding — all the things that matter in production but don't add user-visible features.

**The critical path to production is:**
```
Auth → Secret Key → docker-compose → E2E Tests → Health Checks → Rate Limiting
```

Estimated effort to reach production-ready: **3-4 weeks** for a single developer working full-time, or **1-2 weeks** with the full team.

**Not recommended to deploy to production in current state.** The absence of authentication and the hardcoded secret key alone create unacceptable risk.
