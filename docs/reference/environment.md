# Environment Variable Reference

Every environment variable read by the system, where it is read from, and what it controls.

---

## Files

Settings are loaded by [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
(`apps/backend/src/config/settings.py` → `AppSettings`). It reads, in order:

1. Real environment variables (highest priority)
2. `apps/backend/.env.local` (native dev)
3. `apps/backend/.env`

The root `.env.local` / `.env.production` files are consumed by **Docker Compose** (`env_file:` /
`environment:`) and by the shell scripts — not by the application directly when run in a container.

Templates:

| Template | Copy to | Purpose |
|----------|---------|---------|
| `config/.env.local.example` | `.env.local` (root) | Compose + scripts dev overrides |
| `config/.env.example` | — | General template (legacy) |
| `apps/backend/.env.example` | `apps/backend/.env.local` | Native (non-Docker) backend dev |
| `config/.env.production.example` | `.env.production` | Production deployment |
| `apps/frontend/.env.example` | `apps/frontend/.env.local` | Frontend `NEXT_PUBLIC_*` vars |

> All `.env*` files are gitignored — never commit them.

---

## Application

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT_NAME` | `ProjectLens AI` | Display name used by the app |
| `APP_ENV` | `""` (falls back to `ENV`) | Deployment environment. Prefer `APP_ENV` — `docker-compose.prod.yml` sets it; the settings `environment` property is `APP_ENV or ENV`. Production value: `production`. |
| `ENV` | `development` | Legacy environment field, superseded by `APP_ENV` |
| `DEBUG` | `false` | FastAPI debug mode (stack traces, reload). Must be `false` in prod |
| `LOG_LEVEL` | `INFO` | Logging verbosity: `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `SENTRY_DSN` | `""` (disabled) | Sentry DSN; setting it enables crash + performance reporting. Empty disables Sentry |

## Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/projectlens` | Async SQLAlchemy connection string. Docker infra: host `postgres`. Native dev: `localhost`. Prod: `...?sslmode=require` |

## Cache

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string (used for chat-session state and embedding cache). Prod compose uses `redis://:<password>@redis:6379/0` |

## Auth

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `change-this-in-production` | JWT signing secret. **Fail-fast guard:** in `production` the app refuses to boot with this known-insecure default — generate with `openssl rand -hex 64` |
| `JWT_ALGORITHM` | `HS256` | Signing algorithm |
| `JWT_EXPIRATION_MINUTES` | `60` (dev) / `30` (prod template) | Access-token lifetime |
| `COOKIE_SECURE` | `false` | Marks the auth cookie `Secure`. **Must be `true` in production** (cookie won't be sent over plain HTTP) |

## Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `STORAGE_PROVIDER` | `local` | `local` (disk) or `supabase` (object storage). Prod template: `supabase` |
| `STORAGE_LOCAL_PATH` | `./data/storage` | Base path for local storage (only used when provider is `local`) |

## Supabase (only when `STORAGE_PROVIDER=supabase`)

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPABASE_URL` | `""` | Project URL, e.g. `https://your-project.supabase.co` |
| `SUPABASE_KEY` | `""` | Anon/public key |
| `SUPABASE_SERVICE_KEY` | `""` | Service-role key (used for server-side storage access — keep secret) |
| `SUPABASE_STORAGE_BUCKET` | `reports` | Bucket name |

## File upload

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_UPLOAD_SIZE` | `104857600` (100 MB dev) / `52428800` (50 MB prod) | Max upload bytes |
| `ALLOWED_EXTENSIONS` | `[".pdf", ".docx"]` | Accepted file extensions |

## CORS

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `["http://localhost:3000"]` | JSON list of allowed browser origins. Prod: your frontend domain(s), e.g. `["https://app.yourdomain.com"]` |

## Vector store (ChromaDB)

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMA_HOST` | `localhost` | ChromaDB host. Docker infra: `chroma`. Native dev: `localhost` |
| `CHROMA_PORT` | `8000` | ChromaDB port. Note Docker maps `8001:8000`, so native dev uses `8001` |

## LLM providers

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | `""` | Google AI Studio key (Gemini LLM + Gemini embeddings). Get one free at `https://aistudio.google.com/apikey` |
| `OLLAMA_HOST` | `localhost` | Ollama server host. Compose dev falls back to `host.docker.internal` |
| `OLLAMA_PORT` | `11434` | Ollama server port |
| `OPENCODE_ZEN_API_KEY` | `""` | Optional key for the OpenCode Zen provider (free `deepseek-v4-flash-free` model). Empty = anonymous access |

## User-level preferences (not env)

LLM / embedding / retrieval / chunking selection is stored **per user** in `users.preferences`
(JSON), not in env. The UI settings page (`/settings`) writes them; defaults are
`llm=opencode_zen`, `embedding=gemini`, `retrieval=hybrid`, `chunking=heading_aware`. See
[Database Overview](../database/overview.md).

---

## Reference snippets

```bash
# Generate a production SECRET_KEY
openssl rand -hex 64
```

```bash
# Docker-compose prod requires these (no defaults):
#   POSTGRES_USER, POSTGRES_PASSWORD, REDIS_PASSWORD, SECRET_KEY
# all others fall back to the docker-compose.prod.yml defaults.
```
