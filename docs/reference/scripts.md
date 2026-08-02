# Scripts & Tooling Reference

Every executable in the repo, what it does, and when to run it.

---

## Overview

| Entry point | Purpose |
|-------------|---------|
| `scripts/*.sh` | Day-to-day dev / ops commands (wrapped by the Makefile) |
| `scripts/eval_rag.py` | Automated RAG quality evaluation against ground-truth data |
| `scripts/process_report.py` | Manually re-run the processing pipeline for one report |
| `Makefile` | Friendly aliases for the shell scripts |
| `apps/backend/entrypoint.sh` | Container startup (migrations → uvicorn) |

Run every shell script from the **repo root** — most resolve paths relative to it.

---

## Makefile targets

| Target | Command it runs | Purpose |
|--------|-----------------|---------|
| `make setup` | `scripts/setup.sh` | Install everything (uv deps, npm deps, pre-commit) |
| `make dev` | `scripts/dev.sh` | Start the full dev environment |
| `make build` | `scripts/build.sh` | Build backend + frontend |
| `make lint` | `scripts/lint.sh` | Ruff + mypy + ESLint |
| `make format` | `scripts/format.sh` | Ruff format + Prettier |
| `make test` | `scripts/test.sh` | pytest + npm test |
| `make clean` | inline `rm` | Delete caches / build artifacts |
| `make docker-up` | `docker compose -f docker-compose.yml up -d` | Start dev infrastructure |
| `make docker-down` | `docker compose -f docker-compose.yml down` | Stop dev infrastructure |
| `make docker-reset` | `docker compose -f docker-compose.yml down -v` | Stop + wipe dev volumes |
| `make deploy` | `scripts/deploy.sh` | Production deploy |
| `make prod-up` | `docker compose -f docker-compose.prod.yml up -d --build` | Start prod stack |
| `make prod-down` | `docker compose -f docker-compose.prod.yml down` | Stop prod stack |
| `make prod-logs` | `docker compose -f docker-compose.prod.yml logs -f` | Tail prod logs |

---

## Shell scripts

### `scripts/setup.sh`
One-time environment bootstrap:
1. Install `uv` if missing (`curl ... astral.sh/uv/install.sh`)
2. Copy `config/.env.example` → `.env` if absent
3. `uv sync --extra dev` in `apps/backend` (installs the venv + dev tools)
4. `npm install` in `apps/frontend`
5. `pre-commit install` if available

### `scripts/dev.sh`
The one-command dev environment:
1. Ensure `apps/backend/.env.local` (copy from `apps/backend/.env.example`) and root `.env.local` (from `config/.env.local.example`)
2. `docker compose up -d postgres chroma redis` (infrastructure only — **not** the backend/frontend containers)
3. Wait for Postgres `pg_isready`, Redis `PONG`, ChromaDB heartbeat
4. Run `alembic upgrade head`
5. Start backend: `uv run uvicorn src.main:app --reload --port 8000`
6. Start frontend: `npm run dev`
7. Ctrl+C stops both (trap)

Backend + frontend run **natively** for hot-reload; only Postgres/Chroma/Redis run in Docker.

### `scripts/down.sh`
Stop the dev (or prod, with `--prod`) containers. `-v` / `--volumes` also removes volumes (data loss).

### `scripts/reset.sh`
Full wipe: confirmation prompt → `docker compose down -v` → delete `.env.local` → re-run `dev.sh`.

### `scripts/logs.sh [service]`
Tail compose logs. `--prod` targets the prod compose file. `scripts/logs.sh postgres` for one service.

### `scripts/build.sh`
1. `uv sync --extra dev` in `apps/backend`
2. `npm run build` in `apps/frontend`

### `scripts/lint.sh`
1. `ruff check apps/backend packages/core packages/shared`
2. `mypy` on each package's `src`
3. `npm run lint` in `apps/frontend`

### `scripts/format.sh`
1. `ruff format apps/backend packages/core packages/shared`
2. `npm run format` (Prettier) in `apps/frontend`

### `scripts/test.sh`
1. `uv run pytest -v --tb=short --strict-markers` in `apps/backend`
2. `npm test` in `apps/frontend` (no-op — frontend has no test runner configured)

### `scripts/deploy.sh`
Production deploy (guards + Docker):
1. **Fails** if `.env.production` is missing (prints the copy command)
2. **Fails** if `SECRET_KEY` still contains `replace-with-openssl` or `change-this`
3. `docker compose -f docker-compose.prod.yml build --pull`
4. `docker compose -f docker-compose.prod.yml up -d`
5. Polls `http://localhost/api/v1/health`; fails if unhealthy

### `scripts/backup.sh`
PostgreSQL backup (prod): `pg_dump` inside the postgres container → `./backups/projectlens_<date>.dump`,
keeping the last `BACKUP_KEEP` (default 14). Reads DB credentials from `.env.production`.
Restore: `docker compose -f docker-compose.prod.yml exec -T postgres pg_restore -U $POSTGRES_USER -d $POSTGRES_DB < ./backups/....dump`.
Schedule it via cron, e.g. daily `0 2 * * * cd /path/to/ProjectLens-AI && ./scripts/backup.sh`.

---

## Python scripts

### `scripts/eval_rag.py`
Automated RAG evaluation. Loads ground-truth datasets from `test_data/rag_eval/*.json`, uploads
(optional) the referenced PDFs, asks the chat API each query, and scores answers with an LLM judge.

Metrics produced:
- **Answer quality**: faithfulness, answer relevance, citation precision, overall (0–10)
- **Retrieval** (citation-based): Recall@5/10, MRR@5/10, nDCG@5/10, avg chunks retrieved/cited
- **Latency**: p50 / p95

It POSTs the run to `POST /api/v1/eval/runs` (persisted in the `eval_runs` table) — the file write
to `rag_eval_results.json` was removed in favour of DB persistence.

```bash
# Against a running dev server, using an auth token:
python scripts/eval_rag.py --token <token> --upload --base-url http://localhost:8000

# Reuse already-uploaded reports:
python scripts/eval_rag.py --report-ids "uuid1,uuid2" --token <token>

# Judge provider (scoring LLM): ollama (default) or opencode_zen
#   opencode_zen requires OPENCODE_ZEN_API_KEY to be set
python scripts/eval_rag.py --judge-provider opencode_zen --token <token> --upload
```

### `scripts/process_report.py`
Manual trigger of the processing pipeline for a single report. Imports the backend modules
directly, copies the source PDF into local storage, and runs `ProcessingService.process_report`
with `recursive` chunking.

```bash
python scripts/process_report.py <report-uuid> <path/to/source.pdf>
# defaults: 3fa08aad-e92f-4ef1-9a7a-a1bbcaefe0ec and test_data/StudentGradeHistory_23BCE10311.pdf
```

---

## Container entrypoint

### `apps/backend/entrypoint.sh`
Runs inside the backend container:
1. `alembic upgrade head` (a deploy can never boot against an un-migrated DB)
2. `exec uvicorn src.main:app --host 0.0.0.0 --port 8000`

---

## uv / npm command cheatsheet

```bash
# Backend — all from apps/backend/
uv sync --extra dev                # install deps incl. dev tools
uv sync --frozen --no-dev          # production install (used by Dockerfile)
uv run alembic upgrade head        # apply migrations
uv run uvicorn src.main:app --reload --port 8000
uv run pytest -q                   # tests
uv run ruff check src              # lint
uv run ruff format src             # format
uv run mypy src                    # type check
uv add <package>                   # add dependency
uv add --package <name> <dep>      # add dep to a workspace member
uv run python -c "..."             # run python in the venv

# Frontend — from apps/frontend/
npm install
npm run dev                        # Next.js dev server
npm run build                      # production build
npm run start                      # serve production build
npm run lint                       # ESLint
npm run typecheck                  # tsc --noEmit
npm run format                     # Prettier

# Workspace (repo root)
uv sync                            # installs all workspace members into root .venv
```
