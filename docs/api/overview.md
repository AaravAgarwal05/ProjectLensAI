# API Reference

Base URL: `/api/v1`. OpenAPI docs: `http://localhost:8000/docs` (Swagger), `/redoc`.

---

## Authentication

The backend issues a **JWT delivered as an HttpOnly, SameSite=Lax cookie** (no bearer tokens
in normal use). The frontend sends `credentials: 'include'` on every request; no `Authorization`
header is needed. `/api/v1/auth/login` sets the cookie; `/api/v1/auth/logout` clears it.

All routers except `health` and `auth` mount `Depends(get_current_user)` at the router level —
every endpoint in them requires a valid session. Unauthenticated requests get `401`.

`POST /api/v1/auth/refresh` rotates the token (the frontend service exists but nothing calls it).

---

## Endpoints

### Health — `GET /health`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/health` | ❌ | Comprehensive health: DB `SELECT 1`, ChromaDB heartbeat, Ollama `/api/tags`, Redis `ping`. Returns `status: ok / degraded / down`, version, uptime, per-dependency latency. Rate-limit exempt |

### Auth — `/auth`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/register` | ❌ | Create user (name/email/password). Returns user + sets auth cookie |
| POST | `/api/v1/auth/login` | ❌ | Authenticate, set HttpOnly auth cookie (`Secure` when `COOKIE_SECURE=true`) |
| GET | `/api/v1/auth/me` | ✅ | Current user profile (used by the frontend RouteGuard) |
| POST | `/api/v1/auth/refresh` | ✅ | Rotate the access token |
| POST | `/api/v1/auth/logout` | ✅ | Clear the auth cookie |

### Reports — `/reports`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/reports` | ✅ | Upload a report. **Multipart form**: `file` + `title` + optional `description`, `department`, `author`, `tags` (comma-separated), `visibility` (`private`/`public`/`team`), `year`. Triggers **background processing** (returns `201` immediately) |
| GET | `/api/v1/reports` | ✅ | List caller's reports. Query: `skip`, `limit` (≤100), `status`, `author`, `search` |
| GET | `/api/v1/reports/{report_id}` | ✅ | Single report (owner only; 404 otherwise) |
| PATCH | `/api/v1/reports/{report_id}` | ✅ | Partial metadata update (empty body → 400) |
| DELETE | `/api/v1/reports/{report_id}` | ✅ | Delete report + version files from storage (204) |
| POST | `/api/v1/reports/{report_id}/versions` | ✅ | Upload a new file version → re-triggers background processing |
| GET | `/api/v1/reports/{report_id}/versions` | ✅ | List versions by version number |
| POST | `/api/v1/reports/{report_id}/search` | ✅ | Vector search over the report's indexed chunks. Body `{query, top_k}`; returns ranked chunks with `section_name`, `page_number`, `score` |

### Collections — `/collections`

Named groups of reports.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/collections` | ✅ | Create collection |
| GET | `/api/v1/collections` | ✅ | List collections |
| GET | `/api/v1/collections/{collection_id}` | ✅ | Collection detail |
| PATCH | `/api/v1/collections/{collection_id}` | ✅ | Rename / update |
| DELETE | `/api/v1/collections/{collection_id}` | ✅ | Delete (204) |
| POST | `/api/v1/collections/{collection_id}/reports/{report_id}` | ✅ | Add report to collection |
| DELETE | `/api/v1/collections/{collection_id}/reports/{report_id}` | ✅ | Remove report from collection |

### Chat — `/chat`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/chat/conversations` | ✅ | List chat sessions |
| POST | `/api/v1/chat/conversations` | ✅ | Create session (title, `report_ids`, `mode`) |
| GET | `/api/v1/chat/conversations/{session_id}` | ✅ | Session detail |
| PATCH | `/api/v1/chat/conversations/{session_id}` | ✅ | Update session |
| DELETE | `/api/v1/chat/conversations/{session_id}` | ✅ | Delete session (204) |
| POST | `/api/v1/chat/conversations/{session_id}/archive` | ✅ | Archive session |
| POST | `/api/v1/chat/conversations/{session_id}/restore` | ✅ | Restore archived session |
| GET | `/api/v1/chat/conversations/{session_id}/messages` | ✅ | Message history |
| DELETE | `/api/v1/chat/conversations/{session_id}/messages/{message_id}` | ✅ | Delete a message |
| POST | `/api/v1/chat/send` | ✅ | Ask the RAG pipeline. Body `{message, report_ids, mode}` → answer + `citations`. Rate limit 30/min |
| POST | `/api/v1/chat/send/stream` | ✅ | Same, **streamed**: SSE `data:` lines of `{type:'token'|'done'|'error'}` |

### Settings — `/settings`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/settings/processing-preferences` | ✅ | Current user's processing preferences (chunking/LLM/retrieval/embedding) |
| PUT | `/api/v1/settings/processing-preferences` | ✅ | Partial update of preferences |

### Evaluation — `/eval`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/eval/runs` | ✅ | Persist an eval run (judge/model snapshot, metrics, results) — used by `scripts/eval_rag.py` |
| GET | `/api/v1/eval/runs` | ✅ | List eval runs |
| GET | `/api/v1/eval/runs/{run_id}` | ✅ | Full run incl. config snapshot + per-query results |

### Placeholders

`/documents` and `/analysis` are mounted but **not implemented**:

| Method | Path | Behavior |
|--------|------|----------|
| GET/POST | `/api/v1/documents`, `/api/v1/documents/{id}`, DELETE | Return empty paginated list / placeholder — **unused** (reports are the real upload path) |
| POST | `/api/v1/analysis` | `501 Not Implemented` |
| GET | `/api/v1/analysis/{analysis_id}` | Placeholder |

---

## Error format

Errors use FastAPI's standard shape, surfaced to the frontend as `ApiError { status, code }`:

```json
{ "detail": "Report not found" }
```

HTTP codes used: `400` validation / no-fields, `401` unauthenticated, `404` not found
(also used for cross-owner access — tenancy hides existence, never `403`),
`429` rate limited, `501` not implemented.

---

## Rate limiting

Global rate limits via `slowapi` (`src/api/rate_limiter.py`), backed by Redis. The `/health`
endpoint is exempt. Excess requests → `429`.

| Endpoint | Limit |
|----------|-------|
| `POST /auth/register` | 5/hour |
| `POST /auth/login` | 10/min |
| `POST /chat/send` + `/chat/send/stream` | 30/min |

---

## Middleware stack

Custom ASGI middleware in `src/api/middleware.py`, applied in `main.py`:

| Middleware | Behavior |
|-----------|----------|
| Timing | adds `X-Process-Time` response header |
| SecurityHeaders | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security` when `X-Forwarded-Proto: https` |
| CrossSiteGuard | rejects cross-site mutating requests (`POST`/`PUT`/`PATCH`/`DELETE`) whose `Sec-Fetch-Site` / `Origin` are not same-origin — CSRF defense |

Plus per-app CORS (`CORS_ORIGINS`) and optional Sentry (`SENTRY_DSN`). See
[Backend Services](../backend/services.md) and [Environment](../reference/environment.md).
