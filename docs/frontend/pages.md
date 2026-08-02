# Frontend Pages

Every route in the Next.js App Router, what it renders, and its access level.

> Framework: Next.js 16 App Router, React 19, TypeScript strict, Tailwind + Material-3 token
> system. See [Frontend Architecture](architecture.md) for components, data layer, and state.

---

## Route map

**Public** pages live in `auth/` and the landing page. **Authenticated** pages live in the
`(dashboard)` route group, gated client-side by `RouteGuard` (`GET /auth/me`, redirects to
`/auth/login` on 401). There is no `middleware.ts` — the real boundary is the API's
`get_current_user` dependency; the client guard is defense-in-depth.

| Route | File | Purpose | Access |
|-------|------|---------|--------|
| `/` | `src/app/page.tsx` | Marketing landing: sticky nav, hero, integrations bar, features bento, CTA, footer | Public |
| `/auth/login` | `src/app/auth/login/page.tsx` | Email/password login. "Login with Google" button is UI-only (no handler) | Public |
| `/auth/register` | `src/app/auth/register/page.tsx` | Signup: name/email/password + role picker (cosmetic — role not sent to API) | Public |
| `/auth/forgot-password` | `src/app/auth/forgot-password/page.tsx` | Static form — **no API call** | Public |
| `/auth/reset-password` | `src/app/auth/reset-password/page.tsx` | Password-strength meter + confirm — **no API call** | Public |
| 404 | `src/app/not-found.tsx` | Animated 404 with orbiting-lens visual | Public |
| `/dashboard` | `(dashboard)/dashboard/page.tsx` | Profile home: user card + role badge, account/security/quick-action cards, recent activity (recent chats + reports), logout confirm | Auth |
| `/reports` | `(dashboard)/reports/page.tsx` | Report library: drag-drop upload dropzone, status tabs, department filter, selectable table, bulk delete, pagination, per-row actions (view / chat single / compare / delete) | Auth |
| `/reports/[reportId]` | `(dashboard)/reports/[reportId]/page.tsx` | Report detail: metadata grid, tags, version history, Open-in-Chat / Delete | Auth |
| `/collections` | `(dashboard)/collections/page.tsx` | Collection card grid + inline create-collection card | Auth |
| `/collections/[collectionId]` | `(dashboard)/collections/[collectionId]/page.tsx` | Collection detail: report count, info sidebar, delete | Auth |
| `/chat` | `(dashboard)/chat/page.tsx` | Chat session list with search, New Chat, delete | Auth |
| `/chat/[sessionId]` | `(dashboard)/chat/[sessionId]/page.tsx` | Chat workspace: left session sidebar, streaming message thread, right citations panel | Auth |
| `/settings` | `(dashboard)/settings/page.tsx` | 4-tab settings: Profile (read-only), AI Configuration, Appearance (theme/accent/density), System Status (health poll) | Auth |

> There is **no analytics route** — analytics surfaces only as the dashboard's Recent Activity list.

---

## Page-by-page

### Landing (`/`)
Marketing page. Sticky nav, hero with product positioning, integrations bar, feature bento grid,
CTA, footer. Static content — no data fetching.

### Auth

`auth/layout.tsx` wraps all four auth pages in a dark centered canvas with no app chrome.

- **Login** — inline regex validation, loading spinner on submit, API errors in an error banner.
  On success `router.push('/dashboard')`. The "Login with Google" button has **no handler**.
- **Register** — name/email/password + Student/Teacher role picker. The picker is cosmetic;
  `AuthService.register` sends only name/email/password.
- **Forgot / Reset password** — static UI; no API calls (backend endpoints not implemented).

### Dashboard (`/dashboard`)
Profile home. Shows the current user card with role badge (`admin | user | viewer`), cards for
account/security settings and quick actions, and a Recent Activity list that merges the latest
chats and reports. Logout lives here: `AuthService.logout` → `resetAuth()` → hard
`window.location.href = '/auth/login'`.

### Reports (`/reports`)
The report library and upload surface.

- Drag-drop **dropzone** (`accept=".pdf,.docx,.zip"`) + click-to-browse; upload is disabled while
  in flight; errors surface below the dropzone
- **Status tabs** — reports are filtered by backend status (`uploading / processing / ready /
  error / deleted`; UI groups as draft/ready/archived)
- Department filter, selectable table with bulk delete, pagination
- Per-row actions: **view** (→ detail), **chat single** / **compare** (creates a chat session
  bound to the report id(s) and jumps into chat), **delete** (via `confirmToast`)

### Report detail (`/reports/[reportId]`)
Metadata grid, tags, version history, Open-in-Chat and Delete actions.

### Collections (`/collections`, `/collections/[collectionId]`)
Card grid with an inline create card; detail shows report count, an info sidebar, and delete.
Collections are named groups of reports (backend `collections` table).

### Chat (`/chat`, `/chat/[sessionId]`)
- **List** — searchable session list, New Chat, delete.
- **Workspace** — full-bleed layout (own sidebars, not `DashboardLayout`):
  - left: session sidebar
  - center: message thread with **streaming** responses (SSE `token` chunks appended optimistically)
  - right: citations panel — cited chunks as `SourceCard`s
  - Enter to send, Shift+Enter newline, input disabled while streaming
  - session deletion returns to `/chat`

### Settings (`/settings`)
Four tabs:

- **Profile** — read-only user info
- **AI Configuration** — loads processing preferences via `GET /settings/processing-preferences`,
  dirty-checks against local state, Save → `PUT`. Provider cards render greyed-out with an
  "Under testing" badge for non-GA providers (see [services/settings.ts](../frontend/architecture.md#data-layer))
- **Appearance** — theme (obsidian/zinc/crystal), accent core, density; writes live to
  `data-theme`/`data-accent`/`data-density` on `<html>` + localStorage (`lens.*` keys)
- **System Status** — polls `GET /health` every 30 s

---

## UI/UX flows (end-to-end)

```
Signup/Login ──▶ /dashboard ──▶ upload report (/reports) ──▶ processing ──▶ ready
                                   │
                                   ▼
                             /reports/[id]  ──▶ Open in Chat
                                   │
                                   ▼
                        /chat/[sessionId] ◀── create session (single/compare)
                                   │
                                   ▼
                     streaming answer + citations panel
```

1. **Auth** — login/register → `/dashboard`. Session restored per-mount via `GET /auth/me`
   (HttpOnly cookie; frontend never touches a token).
2. **Upload** — `/reports` dropzone → multipart upload → refetch list; status transitions
   visible via tabs while background processing runs.
3. **Chat** — `/chat` → New Chat → create session (title/report_ids/mode) → workspace; stream
   response, view citations.
4. **Settings** — AI config save → PUT; appearance applies instantly app-wide; system status
   polls health.
