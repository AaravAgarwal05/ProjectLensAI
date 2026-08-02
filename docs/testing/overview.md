# Testing Overview

What is tested, how the suite is wired, and how to run it.

---

## Suite size

| Layer | Files | Tests | Notes |
|-------|-------|-------|-------|
| Backend (`apps/backend/tests`) | 82 | ~796 | pytest, async-native |
| `packages/core/tests` | 1 | 55 | config, events, registry, utils |
| `packages/shared/tests` | 1 | 25 | domain models |
| Frontend (`apps/frontend/src`) | 7 | 58 | Vitest, node env, data layer only |

---

## Backend test layout

Flat root `apps/backend/tests/` (18 files, ~173 tests) covers the report/collection stack and
document processing; subdirectories mirror `src/ai_core/`:

| Directory | Tests | Covers |
|-----------|-------|--------|
| `tests/` (root) | ~173 | auth cookie JWT, security middleware, health, reports/collections API + service + repository, processing pipeline/service/background, parsers, cleaners, metadata |
| `tests/chat/` | ~95 | session manager, message manager, orchestrator, citations, streaming, validation |
| `tests/chunking/` | ~100 | fixed / recursive / heading-aware chunkers, registry, pipeline, validation, hooks |
| `tests/context/` | ~104 | context pipeline, strategies, chunk selection, budget, conversation |
| `tests/embedding/` | ~85 | gemini, ollama, sentence_transformer providers, pipeline, registry, validation |
| `tests/llm/` | ~75 | ollama provider, prompt builder, registry, streaming, validation |
| `tests/retrieval/` | ~89 | dense, hybrid (BM25), multi_query, rerankers (mmr, cross-encoder, none), pipeline |
| `tests/services/` | ~12 | RAGChatService end-to-end with mocked deps |
| `tests/vector_store/` | ~63 | chroma store, pgvector store (failure paths), indexing, registry |

---

## Frontend test layout

`apps/frontend` runs **Vitest** in the node environment (no jsdom). Tests cover the **data
layer** — pure utilities and the HTTP services (query building, snake→camel mappers, FormData
uploads, SSE parsing) — not React components. Config: `vitest.config.ts` (`environment: 'node'`,
`@` → `./src` alias, include `src/**/*.test.ts`). HTTP is mocked by stubbing global `fetch` with
`vi.stubGlobal`; shared helpers live in `src/test/helpers.ts`.

| File | Covers |
|------|--------|
| `src/lib/__tests__/utils.test.ts` | `cn`, `formatDate/DateTime`, `truncate`, `formatBytes`, `generateId` |
| `src/lib/__tests__/api.test.ts` | `apiRequest` — JSON/FormData bodies, 204 → undefined, error envelope → `ApiError`, statusText fallback |
| `src/services/__tests__/auth.test.ts` | login/register/logout/me/refresh + snake→camel user mapper |
| `src/services/__tests__/reports.test.ts` | list (query params + pagination), upload FormData + error codes, update/delete/deleteMany, versions |
| `src/services/__tests__/collections.test.ts` | list/create/update/delete, add/remove report routes |
| `src/services/__tests__/chat.test.ts` | sessions, messages, SSE `streamMessage` (token/done/error/malformed) |
| `src/services/__tests__/settings.test.ts` | preferences fetch + default fallback, provider catalogs |

---

## Test configuration

- **Root `pyproject.toml`**: `testpaths = ["apps/backend/tests", "packages/core/tests", "packages/shared/tests"]`, `addopts = "-v --tb=short --strict-markers"`, `xfail_strict = true`, `filterwarnings = ["error"]`
- **`apps/backend/pyproject.toml`**: `asyncio_mode = "auto"` — async tests need no marker
- **Coverage**: root `[tool.coverage.run]` sources `apps`, `packages`

### Shared fixtures (`tests/conftest.py`)

- `make_report` / `make_version` / `make_collection` — data factories
- `mock_session` — `AsyncMock` of `AsyncSession` (safe execute-chain mocks)
- `mock_storage` — `AsyncMock` of `StorageProvider`
- `mock_settings` — `AppSettings` (100 KiB upload, local storage)
- `client` / `api_client` — ASGI clients; `api_client` overrides `get_db` / `get_current_user` / `get_settings`
- `tests/chat/fixtures.py` — real in-memory **aiosqlite** for chat tables (`pytest_plugins`)
- `tests/llm/fixtures.py` — `MagicMock(spec=httpx.AsyncClient)` + canned responses

### Mocking patterns

- `unittest.mock` (`patch` / `AsyncMock` / `MagicMock`) — ~20 files; HTTP providers mocked with
  `MagicMock(spec=httpx.AsyncClient)` + real `httpx.Response` objects (no respx)
- **No test touches real Postgres** — DB always mocked or in-memory SQLite
- Chroma: `tests/vector_store/test_chroma_store.py` uses a real **ephemeral** `chromadb.Client()`;
  retrieval tests use canned `MagicMock` query dicts
- RAGChatService (`tests/services/test_rag_chat_service.py`): patches
  `build_embedding_provider`, `build_llm_provider`, `_get_chroma_client`, and the Redis cache —
  covers answer flow, multi-report merge, cache hit/miss/fallback

---

## Running tests

```bash
# Backend (the whole suite — 796 tests)
cd apps/backend && uv run pytest -q

# One file / directory
cd apps/backend && uv run pytest tests/retrieval/ -q

# With coverage
cd apps/backend && uv run pytest --cov=src --cov-report=term-missing

# Packages (run from each package dir — see note below)
cd packages/core    && uv run pytest tests/ -q      # 55 tests
cd packages/shared  && uv run pytest tests/ -q      # 25 tests

# Frontend (Vitest, node env — 58 tests)
cd apps/frontend && npm test

# One frontend file
cd apps/frontend && npx vitest run src/services/__tests__/chat.test.ts
```

> **Do not run `uv run pytest -q` from the repo root.** Root `pyproject.toml` lists all three
> `tests/` dirs in `testpaths`, but they are all packages named `tests` — pytest's collection
> makes one shadow the others and the packages suites fail with `No module named 'tests.test_*'`.
> This is a pre-existing repo quirk (CI never runs the root command).

> `make test` (`scripts/test.sh`) runs the backend pytest suite then `npm test` in the frontend —
> both legs now pass. The packages suites are not part of `make test` (run them from their dirs).

CI (`.github/workflows/ci.yml`) provisions real pgvector + redis services, runs
`alembic upgrade head`, then `pytest --cov=src -x` — **from `apps/backend` only**, against them,
though the suite itself never connects (everything is mocked). The package suites are not part
of CI.

---

## Coverage gaps (documented)

- **Frontend: no component or E2E tests** — Vitest covers the data layer (58 tests, node env); React components are untested (no jsdom) and there are no browser tests. CI "test-frontend" is still only `npm run build` (the Vitest suite runs via `npm test` / `make test`, not CI)
- **No true integration tests** against real Postgres/Chroma/Redis — `test_pgvector_store` asserts only graceful-failure paths against a dead DSN
- **`ai_core/eval/`** (LLM judge, `eval_runs` API, `scripts/eval_rag.py`) — untested; the eval script is run manually
- **`ai_core/tracing/`** — untested
- **`ai_core/tokenizer.py`** — live (used by context/budget + LLM providers) but no direct tests
- **API routes** `analysis.py`, `chat.py`, `documents.py`, `eval_runs.py`, `settings.py` — no API-level tests (only health/auth/collections/reports)
- No end-to-end upload→process→index→chat test across the real stack

Known brittleness: root `filterwarnings = ["error"]` + `xfail_strict = true` make the suite
sensitive to deprecation warnings and newly-flaky xfails.
