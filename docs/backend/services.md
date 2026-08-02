# Backend Services

Map of the FastAPI backend: what each service does, who owns what, and how the pieces talk to
each other. Root: `apps/backend/src/`.

```
HTTP request
   │
   ▼
api/v1/* (routers) ── thin: validate, auth, call services
   │
   ├──────────────┬──────────────────────┬──────────────────┐
   ▼              ▼                      ▼                  ▼
services/     ai_core/chat            repository/       storage/
ReportService  orchestrator           CRUD helpers      StorageProvider
ProcessingService                     (per-table)       ├ Local
RAGChatService                                            └ Supabase
CollectionService
   │              │                      │                  │
   └──┬───────────┴──────────┬───────────┴──────────────────┘
      ▼                      ▼
database/ (SQLAlchemy)   ai_core/* (document_processing, chunking,
      │                  embedding, retrieval, context, llm, tracing)
      ▼
PostgreSQL (app data + pgvector in prod)  ·  ChromaDB (dev only)  ·  Redis
```

---

## HTTP layer — `src/api/`

### `v1/router.py`
Mounted under `/api/v1`. All routers except `health` and `auth` carry
`dependencies=[Depends(get_current_user)]`, so every endpoint in them requires a session.
Each router is a separate file (`auth.py`, `reports.py`, `collections.py`, `chat.py`,
`settings.py`, `eval_runs.py`, `health.py`, `documents.py`, `analysis.py`).

### `v1/dependencies.py` — `get_current_user`
Decodes the JWT (python-jose, HS256) from the **`Authorization: Bearer`** header if present,
else the **`auth_token`** cookie. Payload `{sub: user_id, tv: token_version, iat, exp}`, exp 60 min.
Loads the user, rejects if `not is_active` or the JWT `tv` ≠ the user's current `token_version`
(so logout bumps the version and instantly revokes every outstanding token). Any failure → `401`.

### `v1/middleware.py`
ASGI middleware: **Timing** (`X-Process-Time` header), **SecurityHeaders** (nosniff, `DENY`
frame options, HSTS behind `X-Forwarded-Proto: https`), **CrossSiteGuard** (rejects cross-site
`POST/PUT/PATCH/DELETE` via `Sec-Fetch-Site`/`Origin` — CSRF defense). See
[API Overview](../api/overview.md#middleware-stack).

### `v1/rate_limiter.py`
slowapi limiter backed by Redis; keyed on remote address. Exempts `/health`.

---

## Services layer — `src/services/`

| Service | Dependencies | Responsibility |
|---------|--------------|----------------|
| **`ReportService`** | `session, storage, settings` | Report + version CRUD. `_ensure_owned` returns 404 on cross-owner access (never 403 — tenancy hides existence). `_validate_file` checks extension whitelist + size, `_compute_checksum` SHA-256, `_store_file` writes to storage as `reports/{file_id}/{file_id}{ext}` (never the client filename) |
| **`ProcessingService`** | `pipeline, storage, db_factory` | Background document processing (`process_report`): load → status `processing` → download to tempfile → `pipeline.run()` → `_index_document` (chunk → embed → index into the vector store `report_{id}`) → status `ready`; on failure → `error` with message. Tempfile always cleaned. Runs chunking strategy from user prefs (default `heading_aware`), embedding provider (default `ollama`) |
| **`RAGChatService`** | `top_k=5` | Non-streaming `answer(message, report_ids, trace)`: embed query once (Redis-cached, `embedding:{sha256}`, 1h TTL), query the vector store per report, assemble context, generate. Persists a `RequestTrace` fire-and-forget. Used as a fallback when the orchestrator path is unavailable |
| **`CollectionService`** | `session` | Collection CRUD + add/remove report, `_ensure_owned` 404. |

---

## `ai_core/` — the RAG engine

Every subsystem has a **pipeline** (orchestrates a stage with hooks + validation + statistics)
and **strategies/providers** behind a **registry/factory** (`build_*` single selection points).
Consumers depend on the abstract interface, never a concrete provider.

### `chat/` — `ChatOrchestrator`
`process_message()` / `process_message_streaming()` drive one RAG turn:

1. validate + save the user message
2. load conversation history (max 50 msgs)
3. query **rewrite** when history ≥ 3 messages
4. **retrieve** chunks (top_k 25, MMR rerank λ=0.4)
5. assemble **context** (TokenBudgetManager)
6. build prompt → LLM generate (streaming via `streaming.py` SSE)
7. extract **citations** (`CitationEngine`, dedupe by chunk_id, max 10)
8. save assistant message
9. regenerate session **summary** when ≥ 6 messages
10. persist a `RequestTrace`

`SessionManager` / `MessageManager` scope every query by `user_id`. DB models in
`chat/database.py`.

### `tracing/`
`RequestTrace` dataclass (request identity + per-stage ms + chunk/token counts) → `TraceStore`
(`record` / `recent`) with its own DB session; failures swallowed so tracing never breaks chat.
Model `RequestTraceModel` → `request_traces` table.

### `eval/`
`EvalRunModel` → `eval_runs` table; persisted via `POST /eval/runs` by `scripts/eval_rag.py`.
Captures judge/provider/model snapshot + metrics + per-query results.

### `document_processing/`
Offline parse/clean/metadata used by the processing pipeline:

| Module | What it does |
|--------|--------------|
| `pipeline.py` | `ProcessingPipeline.run(file_path)`: parse → clean → metadata → finalize, with `PipelineHook` lifecycle hooks; emits a `ParsedDocument` |
| `parsers/` | `PDFParser` (PyMuPDF, rejects encrypted, per-page text + PDF metadata), `DOCXParser` (python-docx, 20 MB decompression-bomb guard), `TextParser` (txt/md/csv, UTF-8). `ParserRegistry` lazy-instantiates |
| `cleaners/` | `CleaningPipeline` of `WhitespaceCleaner`, `UnicodeCleaner`, `PageArtifactCleaner` |
| `metadata.py` | `MetadataExtractor`: title from filename, author, language heuristic (English-word ratio > 0.15 → `en`), word/char counts, dates, `processed_by="pipeline-v1"` |
| `lifecycle.py` | report status constants + `update_report_status` / `handle_processing_error` |

### `chunking/`
`ChunkingPipeline.run(doc, strategy, config)`: hooks → create chunker → chunk → validate → stats.
Strategies **fixed** / **recursive** / **heading_aware** (registry + factory).
`ChunkingConfiguration`: chunk_size 1000, overlap 200, min 100, max 2000.

### `embedding/`
`EmbeddingPipeline.run(chunks, provider)`: batch embed → validate → statistics. Providers:
`sentence_transformer` (local, lazy import), `ollama` (`nomic-embed-text`, L2-normalizes),
`gemini` (`text-embedding-004`, 768-dim, batch ≤ 100, L2-normalizes).
`build_embedding_provider()` **defaults to gemini**.

### `vector_store/`
`IndexingEngine` (index / delete / delete_by_report / delete_by_version / reindex, batched, 3
retries). `ChromaVectorStore` (HTTP) or `PgVectorStore` (asyncpg, `vector_store` schema, one
table per collection with `vector(dims)` + `content` + `metadata` JSONB columns). `query` /
`fetch_all` on the `VectorStore` ABC are used by **all** retrieval paths; the provider is chosen
by `VECTOR_STORE_PROVIDER` (`chroma` dev default, `pgvector` prod) via `build_vector_store()`.

### `retrieval/`
`RetrievalPipeline` (retriever → reranker → validate). Retrievers: dense, `HybridRetriever`
(dense + inline BM25, k1=1.2 b=0.75), multi_query. Rerankers: `MMRReranker` (λ=0.7 default,
chat uses 0.4), `CrossEncoderReranker` (ms-marco-MiniLM-L-6-v2, graceful fallback when the model
is unavailable), `no_reranker` (default). `RetrieverConfiguration`: dense, top_k 10,
dense/sparse weights 0.5/0.5.

### `context/`
`ContextAssemblyPipeline.run(query, chunks, history, config)`: chunk selection strategy →
metadata enrichment → conversation manager → assemble → `TokenBudgetManager` allocate + enforce
→ validation → `LLMContext`. Strategies: `single_document` (default — strict grounding prompt,
rank + select top 20), `multi_document`, `comparison`, `summary`.

### `llm/`
`LLMProvider` ABC (`generate`, `generate_stream`, `check_health`, `count_tokens`,
`is_model_available`, `configure`). Registry: `google`, `ollama`, `opencode_zen` bundled +
`fallback` registered at bootstrap. `LLMConfiguration` defaults: provider
`os.getenv("LLM_PROVIDER", "opencode_zen")`, model `deepseek-v4-flash-free`, temperature 0.3,
top_p 0.85, max_tokens 4096, context 16384, base_url `https://opencode.ai/zen/v1`,
fallback_models `["llama3.2:1b"]`. `build_llm_provider()` is the single selection point;
`prompt_builder.py` renders system + user prompt with `[Chunk N]` sections and a
`sha256[:16]` prompt hash.

### `tokenizer.py`
tiktoken `estimate_tokens` — **live**: imported by `ai_core/context/budget.py`,
`ai_core/context/conversation.py`, `ai_core/chat/context_truncation.py`, and the LLM providers'
`count_tokens`. No direct unit tests (see [Testing](../testing/overview.md)).

> The legacy `ai_core/registry/`, `ai_core/providers/`, and `ai_core/prompting/` modules
> (`AIPluginRegistry`, `BaseAIProvider`, `PromptManager`) were **removed** — nothing imported
> them; the live paths are the pipelines + `build_*` factories above.

---

## Repository layer — `src/repository/`

`BaseRepository` (generic async CRUD) plus per-table helpers:
`ReportRepository` (`get_by_status` / `get_by_author` / `search` / `get_with_versions` /
`update_status` / `count_by_status`), `CollectionRepository` (`add_report` / `remove_report` /
`get_reports_for_collection`), `VersionRepository` (`get_latest_version` /
`get_next_version_number`).

---

## Storage — `src/storage/`

`StorageProvider` ABC (`store` / `retrieve` / `delete` / `exists`).

| Provider | Notes |
|----------|-------|
| `LocalStorageProvider` | writes under `STORAGE_LOCAL_PATH`; path-traversal guard via resolved-path `startswith` |
| `SupabaseStorageProvider` | lazy client, `service_role` key, auto-creates the bucket, `exists` = prefix list |

Selected at runtime in `reports.py` by `STORAGE_PROVIDER == "supabase"` → Supabase, else local.
See [Environment](../reference/environment.md).

---

## Infrastructure — `src/`

| File | Responsibility |
|------|----------------|
| `config/settings.py` | `AppSettings` (pydantic-settings); loads `.env.local` then `.env`; `get_settings()` singleton; **fails fast** if `environment == "production"` and `SECRET_KEY` is the default |
| `config/logging.py` | console handler, quiets httpx/httpcore |
| `database/session.py` | async engine + `async_session_factory` (pool 10 / overflow 20, `pre_ping`) |
| `infra/redis.py` | async Redis singleton (pool, max 20); `set_json` / `get_json` / `delete_key` / `redis_session` / `health_check_redis` |
| `core/bootstrap.py` | startup wiring, each step try/except with graceful degradation (see below) |

### Startup sequence (`core/bootstrap.py` → `bootstrap_app`)
Runs on app lifespan, after Sentry init (if `SENTRY_DSN`):

1. `configure_logging()`; log version + env
2. `init_db(DATABASE_URL)` — async engine + session factory
3. `get_redis()`
4. register LLM providers (incl. `fallback`) → `app.state.llm_registry`
5. `build_vector_store(settings)` + `health_check()` → `app.state.vector_store` (`None` if down)
6. `build_embedding_provider()` + warmup embed → `app.state.embedding_provider`

`shutdown_app()` closes Redis.

---

## Removed / scaffolding code

**Removed (confirmed unused, no imports anywhere):** `src/auth/` (legacy JWT/passlib — live auth
is `api/v1/dependencies.py` + inline bcrypt), `src/workflows/` (`BaseWorkflow`/`ChatWorkflow` —
superseded by `ai_core/chat` orchestrator), `src/jobs/` (`BaseJob`), `src/memory/`
(`MemoryProvider` + the migration-less `memory_entries` model), `ai_core/providers/`,
`ai_core/registry/`, `ai_core/prompting/`.

Still present but inert:

| Path | Status |
|------|--------|
| `ai_core/chat/database.py::create_tables()` | `create_all` legacy path — **never called**; all tables come from Alembic |
| `v1/documents.py`, `v1/analysis.py` | 501 stubs (documented in [API Overview](../api/overview.md#placeholders)) |
