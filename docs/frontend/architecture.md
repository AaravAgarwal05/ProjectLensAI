# Frontend Architecture

Framework, styling system, components, data layer, and state management.

---

## Framework & tooling

| Area | Choice |
|------|--------|
| Framework | Next.js `^16.3.0-preview.10`, **App Router**, React 19 |
| Language | TypeScript 5.6 strict (`noUncheckedIndexedAccess`, `noUnusedLocals`, `noUnusedParameters`) |
| Path alias | `@/*` → `./src/*` |
| Styling | Tailwind CSS 3.4, `darkMode: 'class'` |
| Build output | `next.config.js`: `output: 'standalone'`, `reactStrictMode: true` |
| Fonts | Geist (sans), JetBrains Mono, Fraunces (logo), Material Symbols Outlined (icons) |

**Scripts** (`apps/frontend/package.json`): `dev`, `build`, `start`, `lint` (eslint),
`format` (prettier), `typecheck` (`tsc --noEmit`), `test` (Vitest, node env — 58 tests over
`src/lib` + `src/services`; see [Testing](../testing/overview.md#frontend-test-layout)).

### Styling: Material-3 token system

`src/app/globals.css` resolves an M3 design-token system at runtime via CSS custom properties on
`<html>`, driven by `data-theme` / `data-accent` / `data-density` attributes. Tailwind colors map
to `rgb(var(--token) / <alpha-value>)` so opacity modifiers work. There are 3 themes
(obsidian default / zinc / crystal), 5 accent cores, and high-density spacing compression.

Theme state lives in `localStorage` under `lens.theme` / `lens.accent` / `lens.density`. The root
layout inlines a pre-paint script that reads those keys and sets the attributes before React
hydrates — this prevents theme flash (FOUC).

---

## Components

### Live kit (imported by pages)

| Component | Purpose |
|-----------|---------|
| `layout/dashboard-layout.tsx` | Sidebar + content shell used by all authed pages except the chat session |
| `layout/sidebar.tsx` | Nav (Dashboard/Reports/Collections/Chat/Settings), active-link highlight via `usePathname` |
| `shared/icon.tsx` | **Icon system** — `<Icon>name</Icon>` wrapping Material Symbols with `fill`/`size` (FONT_VAR settings) |
| `auth/route-guard.tsx` | Client auth gate — `GET /auth/me`, redirects to login on reject |
| `providers/toast-provider.tsx` | Toasts + `confirmToast` (used for deletes) |
| `providers/theme-provider.tsx` | Light/dark/system toggling (secondary to the localStorage mechanism) |
| `ui/button.tsx` | Used only by `shared/error-state.tsx` |

### Dead / legacy kit (not imported anywhere)

Pre-token-system components predating the M3 overhaul — `shared/` (page-header, data-table,
stat-card, section-card, empty-state, error-state, loading-state, search-bar, page-container),
`ui/` (badge, input, select, spinner, tabs), `layout/mobile-nav.tsx`, `layout/command-palette.tsx`.
Two icon systems coexist: Material Symbols (app chrome) and lucide-react (legacy/landing).

---

## Data layer

### `src/lib/api.ts`
`API_BASE = NEXT_PUBLIC_API_URL ?? 'http://localhost:3001/api/v1'` (`.env.local` overrides to
`http://localhost:8000/api/v1`). `apiRequest<T>(path, opts)` — fetch with `credentials: 'include'`
(cookie auth — no Authorization header), JSON body, throws `ApiError { status, code }`, parses the
backend `{error:{message,code}}` shape, returns `undefined` on 204, and lets the browser set
`Content-Type` for FormData.

### `src/services/` (all camelCase → snake_case mappers)

| Service | Endpoints | Notes |
|---------|-----------|-------|
| `auth.ts` | `/auth/login`, `/auth/register`, `/auth/logout`, `/auth/me`, `/auth/refresh` | `forgotPassword`/`resetPassword` are no-op stubs (backend not implemented). `refreshToken` unused |
| `reports.ts` | `/reports` (list/upload/PATCH/DELETE), `/reports/{id}`, `/reports/{id}/versions`, bulk delete | Upload uses raw fetch + FormData (file + title + metadata). Known bug: 401 on upload redirects to `/login` (drops the `/auth` segment) |
| `chat.ts` | `/chat/conversations`, `/chat/sessions/...`, `/chat/send`, `/chat/send/stream` | `streamMessage` is a manual SSE reader over POST, parsing `{type:'token'|'done'|'error'}` |
| `collections.ts` | `/collections` CRUD + `/collections/{id}/reports/{rid}` | add/remove report |
| `settings.ts` | `/settings/processing-preferences` (GET/PUT) | Also exports the option catalogs + `DEFAULT_PREFERENCES`; providers with `status:'testing'` render greyed-out |

`src/lib/utils.ts` — `cn` (clsx + tailwind-merge), `formatDate`, `formatDateTime`, `truncate`,
`formatBytes`, `generateId`.

---

## State management

- **Zustand stores** (`src/stores/`): `auth-store` (user, isAuthenticated — actually used by
  dashboard/sidebar/settings), `sidebar-store` (collapse state). **Unused:** `chat-store`,
  `reports-store`, `settings-store`, `theme-store`.
- **No React Query** — declared in package.json but never imported. All data fetching is
  `useEffect` + local `useState` + service calls. Chat uses optimistic local state + streaming chunks.
- Providers composed in `src/app/providers.tsx`: `ThemeProvider` + `ToastProvider`.
- **Session is not persisted client-side** — restored by `GET /auth/me` on each mount.

---

## Auth

Session = **HttpOnly cookie** set by the backend. Every request sends `credentials: 'include'`.
`RouteGuard` (client) plus each page's own `getCurrentUser` re-hydration; a 401/expiry on the
dashboard triggers `resetAuth()` + redirect to login. Roles: `admin | user | viewer`
(`src/types/user.ts`).

No multi-tenant/org concept in the frontend — the only sharing flag is report `visibility`
(`private/public/team`, `src/types/report.ts`).

---

## Known debt

- `@tanstack/react-query`, `react-hook-form`, `zod`, `@hookform/resolvers` declared but **unused**
- Register page role picker is cosmetic (role never sent)
- Forgot/reset password are static UI
- `shared/` + `ui/` component kits and 4 of 6 zustand stores are dead code
- `eslint-config-next` `^15.0.0` mismatches Next 16
