# Getting Started

## Quick Start

For a detailed step-by-step guide, see [Development Run Guide](run-dev.md).

```bash
./scripts/dev.sh
```

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose v2
- [uv](https://docs.astral.sh/uv/) (package manager) — `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Manual Setup

```bash
# 1. Environment
cp config/.env.local.example .env.local

# 2. Start infrastructure (PostgreSQL, ChromaDB, Redis)
docker compose -f docker-compose.yml up -d

# 3. Install backend
cd apps/backend
uv sync --extra dev
uv run alembic upgrade head
cd ../..

# 4. Install frontend
cd apps/frontend
npm install
cd ../..

# 5. Start development servers (separate terminals)
cd apps/backend && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
cd apps/frontend && npm run dev
```

## Common Commands

| Command | Description |
|---------|-------------|
| `./scripts/dev.sh` | Full dev environment (one command) |
| `make setup` | Install all dependencies |
| `make dev` | Start development servers |
| `make test` | Run all tests |
| `make lint` | Run all linters |
| `make build` | Build for production |
| `make docker-up` | Start Docker infrastructure |
| `make docker-down` | Stop Docker infrastructure |
