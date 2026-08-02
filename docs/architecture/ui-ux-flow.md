# UI/UX Flows

End-to-end user journeys and the system state they touch. Per-route render details live in
[Frontend Pages](../frontend/pages.md); data layer in [Frontend Architecture](../frontend/architecture.md);
the backend side of each flow in [AI Pipeline](ai-pipeline.md) and [API Reference](../api/overview.md).

```
Signup/Login ─▶ /dashboard ─▶ upload report (/reports) ─▶ processing ─▶ ready
                                  │
                                  ▼
                            /reports/[id] ─▶ Open in Chat
                                  │
                                  ▼
                    /chat/[sessionId] ◀─ New Chat / chat single / compare
                                  │
                                  ▼
                     streaming answer + citations panel
```

---

## 1. Authentication & session restore

1. **Register** (`/auth/register`) → `POST /auth/register` → backend sets the HttpOnly cookie →
   `router.push('/dashboard')`. The role picker is **cosmetic** (role never sent).
2. **Login** (`/auth/login`) → `POST /auth/login` → cookie set → `/dashboard`. The "Login with
   Google" button has **no handler**.
3. **Session restore** — every authed page mount calls `GET /auth/me` (RouteGuard + per-page
   re-hydration). A `401` triggers `resetAuth()` + redirect to `/auth/login`.
4. **Logout** — dashboard → `AuthService.logout` → `POST /auth/logout` (bumps `token_version`,
   revoking every outstanding JWT) → `resetAuth()` → hard `window.location.href = '/auth/login'`.

Frontend never touches the token: auth is the cookie + `credentials: 'include'` on every fetch.

## 2. Upload & processing (the core loop)

1. `/reports` dropzone accepts `.pdf .docx .zip` (drag-drop + click-to-browse).
2. `POST /reports` multipart (`file` + `title` + optional metadata) — returns `201` immediately;
   the backend kicks off `ProcessingService.process_report` **in the background**.
3. Frontend refetches the list; **status tabs** show the transition:
   `uploading → processing → ready` (or `error`, surfaced with a message).
4. Background work: parse → clean → metadata → chunk (default `heading_aware`) → embed →
   index Chroma (`report_{id}`). Per-version reprocessing on `POST /reports/{id}/versions`.
5. A new report is chat-ready the moment its status is `ready`.

> Upload UX quirk (known): a 401 on upload redirects to `/login` and **drops the `/auth`
> segment** (goes to `/login` instead of `/auth/login`). Frontend debt — see
> [architecture.md](../frontend/architecture.md#data-layer).

## 3. Report library & detail

- **List** (`/reports`): status tabs, department filter, search, paginated selectable table,
  bulk delete. Per-row actions: view, chat single, compare, delete (`confirmToast`).
- **Detail** (`/reports/[id]`): metadata grid, tags, version history (with re-upload),
  Open-in-Chat, Delete.
- **Delete** cascades: report row + version files in storage (204).
- **Search**: `POST /reports/{id}/search` runs vector search over that report's chunks and
  returns ranked hits with section/page/score — the backend for an in-document search.

## 4. Collections

- `/collections`: card grid + inline create card.
- `/collections/[id]`: report count, info sidebar, delete.
- Add/remove a report: `POST/DELETE /collections/{id}/reports/{rid}`.
- Collections exist to bundle reports for multi-report chat (compare mode).

## 5. Chat (the RAG experience)

1. `/chat` list → **New Chat** → `POST /chat/conversations` (`title`, `report_ids`, `mode`).
2. Workspace `/chat/[sessionId]` is **full-bleed** (own sidebars, not the dashboard layout):
   - left: session list (switch / delete)
   - center: streaming message thread — SSE `token` chunks appended optimistically
   - right: citations panel — cited chunks as `SourceCard`s
3. Send: Enter (Shift+Enter newline); input disabled while streaming.
4. Backend per turn: rewrite → retrieve (top_k 25, MMR) → context (TokenBudgetManager) →
   prompt → LLM → citations (≤ 10, deduped) → save → summary refresh (≥ 6 msgs).
5. Session archive/restore (`/archive`, `/restore`); delete returns to `/chat`.

## 6. Settings

- **Profile** — read-only user info.
- **AI Configuration** — `GET/PUT /settings/processing-preferences`: chunking strategy,
  LLM provider/model, retrieval strategy, embedding provider/model, top_k, etc. Dirty-checked
  local state → Save. Providers in `status: 'testing'` render greyed-out.
- **Appearance** — theme / accent / density → live `data-*` attributes + `localStorage`; applied
  pre-hydration to avoid theme flash.
- **System Status** — polls `GET /health` every 30 s: DB / Chroma / Ollama / Redis →
  `ok / degraded / down`.

## 7. System health & ops

`GET /health` (rate-limit exempt) returns `status`, version, uptime, per-dependency latency.
Used by the Settings System Status tab and by uptime monitors. See
[Deployment](../deployment/overview.md#keepalive--free-tier-notes).

---

## State machine summary

```
Report:   uploading ─▶ processing ─▶ ready
                      └────────────▶ error
Session:  active ─▶ archived ─▶ restored
User:     logged-out ─▶ logged-in (cookie) ─▶ logged-out (token_version bumped)
```
