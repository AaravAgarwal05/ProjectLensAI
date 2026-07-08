# ProjectLens AI

**Production-grade document analysis platform**

![Python 3.12](https://img.shields.io/badge/python-3.12-blue)
![Next.js 14](https://img.shields.io/badge/next.js-14-black)
![License MIT](https://img.shields.io/badge/license-MIT-green)

---

## Overview

ProjectLens AI is a full-stack, production-grade document analysis platform that combines the power of modern AI with a robust, scalable backend. It enables users to upload, analyze, and compare documents across multiple AI providers, chat with their documents, and collaborate in a shared workspace.

The platform is built with a clean layered architecture, a provider-agnostic AI layer, and asynchronous processing from the ground up — designed for extensibility, testability, and real-world deployment.

---

## Architecture

ProjectLens AI follows a clean layered architecture with strict dependency direction. The core design centers on a plugin registry pattern for AI providers, async-first processing pipelines, and a versioned REST API.

[Read the full architecture documentation →](docs/architecture/overview.md)

---

## Project Structure

```
ProjectLens-AI/
├── apps/
│   ├── backend/          # FastAPI application
│   │   ├── app/
│   │   │   ├── api/      # Route handlers (v1)
│   │   │   ├── core/     # Workflows, services, repos
│   │   │   └── ai/       # Chunking, embedding, LLM
│   │   ├── alembic/      # Database migrations
│   │   └── tests/
│   └── frontend/         # Next.js 14 application
│       └── src/
│           ├── app/      # App router pages
│           └── components/
├── packages/
│   ├── core/             # Shared domain logic
│   └── shared/           # DTOs, schemas, types
├── docs/                 # Documentation
│   ├── architecture/
│   ├── development/
│   ├── api/
│   ├── database/
│   └── deployment/
├── docker/               # Docker configs
├── scripts/              # Utility scripts
├── docker-compose.yml
└── Makefile
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose v2

### One-Command Setup (Recommended)

```bash
git clone <repo-url>
cd ProjectLens-AI
./scripts/dev.sh
```

This starts PostgreSQL, ChromaDB, Redis via Docker, runs migrations, and launches backend + frontend.

### Manual Setup

```bash
# 1. Environment
cp .env.local.example .env.local

# 2. Start infrastructure
docker compose -f docker-compose.dev.yml up -d

# 3. Backend
cd apps/backend
pip install -e ".[dev]"
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 4. Frontend
cd apps/frontend
npm install
npm run dev
```

### Service URLs

| Service     | URL                                                    | Docker Service     |
| ----------- | ------------------------------------------------------ | ------------------ |
| PostgreSQL  | `postgresql://postgres:postgres@localhost:5432/projectlens` | `postgres:5432`    |
| ChromaDB    | `http://localhost:8001`                                | `chroma:8000`      |
| Redis       | `redis://localhost:6379`                               | `redis:6379`       |
| Backend API | `http://localhost:8000`                                | `backend:8000`     |
| API Docs    | `http://localhost:8000/docs`                           | `backend:8000`     |
| Frontend    | `http://localhost:3000`                                | `frontend:3000`    |

### Helper Commands

| Command                        | Description                              |
| ------------------------------ | ---------------------------------------- |
| `./scripts/dev.sh`             | Full dev environment (infra + services)  |
| `./scripts/down.sh`            | Stop infrastructure                      |
| `./scripts/down.sh -v`         | Stop and remove volumes                  |
| `./scripts/reset.sh`           | Full reset (data loss!)                  |
| `./scripts/logs.sh [service]`  | View logs                                |
| `make setup`                   | Install all dependencies                 |
| `make dev`                     | Start development servers                |
| `make test`                    | Run all tests                            |
| `make lint`                    | Run linters                              |

---

## Features

- **Document Analysis** — Upload and analyze documents with configurable pipelines
- **AI-Powered Insights** — Leverage multiple AI providers (OpenAI, Claude, Ollama, and more)
- **Comparative Analysis** — Compare documents side by side
- **Chat Interface** — Conversational querying over your documents
- **Collaborative Workspace** — Share and collaborate on analysis results

---

## Tech Stack

| Category          | Technology                                      |
|-------------------|-------------------------------------------------|
| Backend           | FastAPI, SQLAlchemy 2.0, Celery                |
| Frontend          | Next.js 14, TypeScript, Tailwind CSS           |
| Database          | PostgreSQL 16 + pgvector, Redis                |
| AI                | Provider-agnostic (OpenAI, Claude, Ollama, …)  |
| Infrastructure    | Docker, Docker Compose, Nginx                  |

---

## Development

```bash
make setup    # Install all dependencies
make dev      # Start development servers
make lint     # Run linters (Ruff, mypy, ESLint)
make test     # Run all tests
make build    # Build for production
```

---

## Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

| Guide | Location | Description |
|-------|----------|-------------|
| Development Run Guide | [`docs/development/run-dev.md`](docs/development/run-dev.md) | Full dev environment setup and troubleshooting |
| Getting Started | [`docs/development/getting-started.md`](docs/development/getting-started.md) | Prerequisites and basic setup |
| Production Run Guide | [`docs/deployment/run-production.md`](docs/deployment/run-production.md) | Production deployment, security, and maintenance |
| Deployment Overview | [`docs/deployment/overview.md`](docs/deployment/overview.md) | Architecture and deployment options |
| API Reference | [`docs/api/overview.md`](docs/api/overview.md) | REST API endpoints and schemas |
| Architecture | [`docs/architecture/overview.md`](docs/architecture/overview.md) | Layered architecture and patterns |
| Database | [`docs/database/overview.md`](docs/database/overview.md) | Schema, migrations, and vector search |

---

## Production Readiness

### ✅ Implemented

| Area | Status | Details |
|------|--------|---------|
| Containerization | ✅ | Docker Compose dev + prod, health checks, resource limits |
| Database | ✅ | PostgreSQL 16 + pgvector, Alembic migrations, async SQLAlchemy |
| API Security | ✅ | JWT auth (HS256), CORS config, password hashing (bcrypt) |
| File Storage | ✅ | Local + Supabase providers, extension/size validation |
| Document Processing | ✅ | PDF, DOCX, TXT parsing; text cleaning pipeline; metadata extraction |
| Background Processing | ✅ | FastAPI BackgroundTasks, processing pipeline |
| AI Core | ✅ | Plugin registry for LLM providers, embedding, chunking, retrieval |
| Testing | ✅ | 190+ tests across all modules, pytest fixtures |
| CI/CD | ✅ | GitHub Actions, lint (ruff, mypy), test, release workflow |

### 🚧 Pre-Production Checklist

Before deploying to production, address these items:

- [ ] **Strong SECRET_KEY**: Generate via `openssl rand -hex 64`, never use defaults
- [ ] **Database SSL**: Enable `?sslmode=require` in `DATABASE_URL`
- [ ] **TLS Termination**: Configure HTTPS via Nginx + Let's Encrypt or reverse proxy
- [ ] **Rate Limiting**: Add Nginx `limit_req` or middleware rate limits
- [ ] **Sentry/Monitoring**: Add error tracking (Sentry, DataDog, etc.)
- [ ] **DB Connection Pooling**: Tune `pool_size` / `max_overflow` in async SQLAlchemy
- [ ] **Graceful Shutdown**: Verify lifecycle hooks drain background tasks
- [ ] **Load Testing**: Benchmark with locust/k6 before production traffic
- [ ] **Backups**: Automated daily PostgreSQL + volume backups
- [ ] **Secrets Rotation**: Process for rotating SECRET_KEY and Supabase keys

### 📊 Architecture Maturity

| Layer | Pattern | Maturity |
|-------|---------|----------|
| API | RESTful versioned (v1), FastAPI | 🟢 Production |
| Service | Dependency injection, no global state | 🟢 Production |
| Repository | SQLAlchemy async, base CRUD | 🟢 Production |
| Processing | Plugin registry, background pipeline | 🟡 Needs edge-case hardening |
| AI Core | Provider-agnostic, registry pattern | 🟡 Needs LLM provider implementation |
| Storage | Strategy pattern (local, supabase) | 🟢 Production |
| Auth | JWT + bcrypt, middleware | 🟢 Production |

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
