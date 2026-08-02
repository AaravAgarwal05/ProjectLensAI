# Database Overview

PostgreSQL 16. Schema is managed **exclusively by Alembic migrations** — the app never calls
`create_all`. Models live in `apps/backend/src/database/models/` (SQLAlchemy 2.0 `Mapped[...]`
typed columns); chat/trace/eval tables have their models in `src/ai_core/chat/database.py`,
`src/ai_core/tracing/database.py`, `src/ai_core/eval/database.py`.

> **Init SQL.** `docker/postgres/init/01-init.sql` only enables the pgvector extension. The
> earlier-design `documents` / `document_chunks` tables it used to create were **removed** —
> nothing read or wrote them; the real schema comes from Alembic.

---

## Connection & sessions

- Async engine + `async_session_factory` in `src/database/session.py` (asyncpg driver; pool 10,
  overflow 20, `pre_ping`).
- `DATABASE_URL` from env (see [Environment](../reference/environment.md)).
- API request sessions via FastAPI `Depends(get_db)` — created per request, closed after.
- Background workers (document processing, trace persistence) open their **own** session from
  `async_session_factory()` instead of the request session.

---

## Tables

### `users`
Identity + per-user processing preferences.

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | `gen_random_uuid()` |
| `email` | varchar unique | login identity |
| `name` | varchar | display name |
| `hashed_password` | varchar | bcrypt hash (never plaintext) |
| `role` | varchar | `admin` / `user` / `viewer` |
| `is_active` | bool | soft-disable; 401 when false |
| `token_version` | int | server_default `0`; bumped on logout to invalidate all issued JWTs |
| `preferences` | JSON (JSONB on PG) | `ProcessingPreferences` — `chunking_strategy`, `llm_provider`, `llm_model`, `retrieval_strategy`, `embedding_provider`, `chunk_size`, `chunk_overlap`, `min_chunk_size`, `embedding_model`, `top_k` |

`DEFAULT_PREFERENCES` defaults `embedding_provider = "gemini"` /
`embedding_model = "text-embedding-004"`, matching the frontend catalog and
`EmbeddingConfiguration`. (Previously the backend default was `ollama` while everything else
said `gemini` — aligned 2026-08-02. Users registered before then keep their stored `ollama`
preference until they change it in Settings.)

### `reports`
A user's uploaded document — the tenant root object.

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | |
| `owner_id` | uuid FK → `users.id` (indexed) | **added by migration `b2c3d4e5f6a7`** — tenancy boundary |
| `title` | varchar (indexed) | |
| `description` | text | optional |
| `department` | varchar | filter |
| `author` | varchar | optional |
| `tags` | ARRAY(text) | |
| `visibility` | varchar | `private` / `public` / `team` |
| `year` | int | optional |
| `status` | varchar (indexed) | lifecycle: `uploading` → `processing` → `ready` / `error` |
| `error_message` | text | set when status is `error` |
| `storage_provider` | varchar | records which provider stored the file — set from `STORAGE_PROVIDER` at upload time (model default `"local"`) |
| `storage_path` | varchar | provider-relative file path |
| `original_filename` | varchar | |
| `mime_type` | varchar | |
| `checksum` | varchar | SHA-256 |
| `file_size` | bigint | |
| `created_at` / `updated_at` | timestamptz | |

### `report_versions`
One row per uploaded file version of a report.

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | |
| `report_id` | uuid FK → `reports.id` (CASCADE) | |
| `version_number` | int | unique per report |
| `storage_path` | varchar | |
| `original_filename` | varchar | |
| `mime_type` | varchar | |
| `checksum` | varchar | |
| `file_size` | bigint | |
| `created_at` | timestamptz | |

### `collections`
Named groups of reports (tenant-scoped).

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | |
| `owner_id` | uuid FK → `users.id` | migration `b2c3d4e5f6a7` |
| `name` | varchar unique | |
| `description` | text | optional |
| `created_at` | timestamptz | |

### `collection_reports`
Join table: many-to-many collections ↔ reports. Composite PK `(collection_id, report_id)`,
both FKs CASCADE.

### `chat_sessions`
RAG conversation sessions.

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | |
| `user_id` | uuid FK → `users.id` | |
| `title` | varchar | |
| `report_ids` | jsonb | reports the session is bound to |
| `mode` | varchar | single / compare / collection |
| `is_archived` | bool | |
| `summary` | text | migration `7b1bc9b75c6a` |
| `created_at` / `updated_at` | timestamptz | |

### `chat_messages`
Per-session message history.

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | |
| `session_id` | uuid FK → `chat_sessions.id` | |
| `role` | varchar | `user` / `assistant` |
| `content` | text | |
| `citations` | jsonb | source chunks cited by the answer |
| `created_at` | timestamptz | |

### `request_traces`
Per-request RAG observability rows (migration `8c1e2f3a4b5c`). Written fire-and-forget by
`TraceStore`; failures swallowed.

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | |
| `request_id` | varchar | correlation id |
| `user_id` | uuid | |
| `session_id` | uuid | |
| `prompt_version` | varchar | versioned prompt used |
| `prompt_hash` | varchar | sha256 of the rendered prompt |
| `model` / `provider` | varchar | LLM identity |
| `cache_hit` | bool | |
| `stages` | jsonb | per-stage latencies (rewrite/embed/retrieve/llm/…) |
| `counts` | jsonb | chunks retrieved/cited, token counts |
| `created_at` | timestamptz | |

### `eval_runs`
Persisted LLM-judge evaluation runs (migration `9d0e1f2a3b4c`).

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid PK | |
| `judge_provider` / `judge_model` | varchar | judge identity |
| `llm_model` | varchar | model under test |
| `embedding_model` | varchar | |
| `retrieval_top_k` | int | config snapshot |
| `mmr_lambda` | float | config snapshot |
| `prompt_version` | varchar | |
| `overall` | float | aggregate score |
| `metrics` | jsonb | per-metric scores |
| `results` | jsonb | per-query results |
| `created_at` | timestamptz | |

---

## Alembic migration chain

`apps/backend/alembic/versions/` — linear chain, head **`b2c3d4e5f6a7`**:

```
3f62cab78965  reports, report_versions, collections, collection_reports
782274bc742a  users
2b4c1e9d7a3f  user preferences (JSON column)
4d1e8f2a6c3b  chat_sessions, chat_messages
7b1bc9b75c6a  chat_sessions.summary
8c1e2f3a4b5c  request_traces
9d0e1f2a3b4c  eval_runs
a1b2c3d4e5f6  users.token_version
b2c3d4e5f6a7  reports.owner_id + collections.owner_id   ← HEAD
```

Apply:

```bash
uv run --package projectlens-backend alembic upgrade head
```

`entrypoint.sh` runs this on container start before uvicorn, so migrations are automatic in
Docker. **Remaining schema note:** `ai_core/chat/database.py::create_tables()` still calls
`create_all`, but it is **never invoked** — all tables come from Alembic. (The migration-less
`memory_entries` model was removed with the dead `src/memory/` module.)

---

## Vector store — not in Postgres

Embeddings live in **ChromaDB** (separate service, port `8001`), not pgvector. Chroma collections
are per report (`report_{id}`); metadata carries `chunk_id`, `report_id`, `version_id`,
`embedding_model`, `provider`. A pgvector store (`src/ai_core/vector_store/pgvector_store.py`)
exists but is **not wired up** — the store registry defaults to Chroma. See
[AI Pipeline](../architecture/ai-pipeline.md).
