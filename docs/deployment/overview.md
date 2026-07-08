# Deployment Overview

## Guides

| Guide | Description |
|-------|-------------|
| [Production Run Guide](run-production.md) | Full production deployment walkthrough |
| [Development Run Guide](../development/run-dev.md) | Local development setup |

## Quick Reference

### Development Stack

```bash
# Start infrastructure
docker compose -f docker-compose.dev.yml up -d

# Stop
./scripts/down.sh

# Full reset
./scripts/reset.sh
```

Services: PostgreSQL 16 + pgvector, ChromaDB, Redis 7

### Production Stack

```bash
# Deploy
cp .env.production.example .env.production
# ... edit .env.production with real values ...
./scripts/deploy.sh

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Update
git pull && docker compose -f docker-compose.prod.yml up -d --build
```

Services: Nginx, Backend (FastAPI), Frontend (Next.js), PostgreSQL, Redis

## Architecture

```
Development:                       Production:
┌──────────┐                      ┌──────────┐
│  Backend │──► PostgreSQL        │  Nginx   │──► Backend  ──► PostgreSQL
│  :8000   │──► ChromaDB          │  :80     │──► Frontend ──► Redis
│          │──► Redis             │  (TLS)   │
├──────────┤                      ├──────────┤
│  Frontend│                      │  Docker  │
│  :3000   │                      │  Compose │
├──────────┤                      └──────────┘
│  Docker  │
│  Compose │
└──────────┘
```

## Environment Variables

| File | Purpose |
|------|---------|
| `.env.example` | Template with all variables documented |
| `.env.local.example` | Development defaults |
| `.env.local` | Local dev overrides (gitignored) |
| `.env.production.example` | Production template |
| `.env.production` | Production secrets (gitignored) |

## Production Checklist

- [ ] Generate strong `SECRET_KEY`: `openssl rand -hex 64`
- [ ] Set `DEBUG=false` and `APP_ENV=production`
- [ ] Configure TLS/HTTPS (Let's Encrypt or reverse proxy)
- [ ] Restrict `CORS_ORIGINS` to your domain(s)
- [ ] Set up automated database backups
- [ ] Configure health check monitoring
- [ ] Enable rate limiting at Nginx level
- [ ] Harden firewall (only ports 80/443 open)
