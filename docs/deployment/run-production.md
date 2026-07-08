# Production Run Guide

> **Last updated:** 2026-07-08
> **Target:** Production server (Linux amd64)

---

## Overview

This guide covers deploying ProjectLens AI in production using Docker Compose. The production stack runs all services in containers behind an Nginx reverse proxy with resource limits, restart policies, and no hot-reload.

---

## Prerequisites

| Requirement | Version | Check Command |
|------------|---------|---------------|
| Linux server | Ubuntu 22.04+ / Debian 12+ | `cat /etc/os-release` |
| Docker | 24+ | `docker --version` |
| Docker Compose | v2 | `docker compose version` |
| CPU | 2+ cores | `nproc` |
| RAM | 4+ GB | `free -h` |
| Disk | 20+ GB free | `df -h` |
| Domain (optional) | DNS A record pointing to server | `dig +short yourdomain.com` |

---

## Quick Deploy

```bash
# 1. Clone
git clone <repo-url>
cd ProjectLens-AI

# 2. Environment
cp .env.production.example .env.production
# EDIT .env.production with real values (see below)

# 3. Deploy
./scripts/deploy.sh
```

---

## Step-by-Step

### 1. Environment Configuration

Edit `.env.production` with your production values:

```bash
nano .env.production
```

**Required variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string (with SSL) | `postgresql+asyncpg://user:pass@host:5432/db?sslmode=require` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `SECRET_KEY` | Strong JWT signing key (64+ hex chars) | *(see below)* |
| `CORS_ORIGINS` | Allowed frontend domains | `["https://app.yourdomain.com"]` |

**Generate a secure SECRET_KEY:**

```bash
# Generates 64 random hex characters
openssl rand -hex 64
```

**Optional variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `MAX_UPLOAD_SIZE` | `52428800` | Max file upload in bytes (50 MB) |
| `ALLOWED_EXTENSIONS` | `.pdf,.docx` | Accepted file extensions |
| `STORAGE_PROVIDER` | `supabase` | File storage backend |
| `SUPABASE_URL` | — | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | — | Supabase service role key |

### 2. Build and Start

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

This builds and starts:

| Service | Container Name | Port | Restart | Resource Limits |
|---------|---------------|------|---------|----------------|
| Nginx | `projectlens-nginx` | `80` (host) → `80` (container) | `always` | default |
| PostgreSQL 16 + pgvector | `projectlens-postgres` | internal | `always` | 1 GB RAM, 1 CPU |
| Redis 7 + AOF | `projectlens-redis` | internal | `always` | 512 MB RAM, 0.5 CPU |
| Backend (FastAPI) | `projectlens-backend` | `8000` (internal) | `always` | 1 GB RAM, 1 CPU |
| Frontend (Next.js) | `projectlens-frontend` | internal | `always` | default |

### 3. Verify Deployment

```bash
# Check all containers are running
docker compose -f docker-compose.prod.yml ps

# Check health endpoint
curl http://localhost/api/v1/health

# Check Nginx is responding
curl -I http://localhost
```

### 4. Set Up TLS (HTTPS)

**Option A: Let's Encrypt with certbot**

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal (certbot adds a systemd timer by default)
sudo certbot renew --dry-run
```

**Option B: Reverse proxy (recommended for multi-service)**

Place Nginx behind a cloud reverse proxy (Cloudflare, AWS ALB, etc.) and handle TLS at the proxy layer.

---

## Production Architecture

```
                          ┌─────────────┐
                          │   Internet  │
                          └──────┬──────┘
                                 │ :80 / :443
                          ┌──────▼──────┐
                          │    Nginx    │  ← TLS termination, static assets
                          └──────┬──────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼─────┐ ┌───▼────┐ ┌────▼─────┐
              │  Backend  │ │Postgres│ │  Redis   │
              │  :8000    │ │ :5432  │ │ :6379    │
              └─────┬─────┘ └────────┘ └──────────┘
                    │
              ┌─────▼─────┐
              │  Frontend │
              │  :3000    │
              └───────────┘
```

---

## Maintenance

### View Logs

```bash
docker compose -f docker-compose.prod.yml logs -f      # all services
docker compose -f docker-compose.prod.yml logs -f backend  # single service
```

### Update Deployment

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

### Database Backups

```bash
# Manual backup
docker exec projectlens-postgres pg_dump -U postgres projectlens > backup_$(date +%Y%m%d).sql

# Restore
cat backup.sql | docker exec -i projectlens-postgres psql -U postgres -d projectlens
```

### Stop Services

```bash
docker compose -f docker-compose.prod.yml down           # stop
docker compose -f docker-compose.prod.yml down -v        # stop + wipe volumes
```

### Health Monitoring

```bash
# Basic health check
curl -f http://localhost/api/v1/health || echo "Backend unhealthy"

# Container resource usage
docker stats
```

---

## Security Checklist

- [ ] **SECRET_KEY**: Generated via `openssl rand -hex 64`, not the default
- [ ] **Database password**: Strong, unique password, not `postgres`
- [ ] **TLS/HTTPS**: Enabled for all traffic
- [ ] **CORS**: Restricted to specific frontend domains
- [ ] **Rate limiting**: Configured at Nginx or application level
- [ ] **File uploads**: Limited to `.pdf`, `.docx` — max 50 MB
- [ ] **Docker non-root**: Services run as non-root user where possible
- [ ] **Security updates**: Regular `docker compose pull` for base images
- [ ] **Backups**: Automated daily database backups
- [ ] **Monitoring**: Health check endpoint monitored (PagerDuty, etc.)
- [ ] **Firewall**: Only ports 80/443 open to public; 5432/6379 closed

---

## Environment Variable Reference

| Variable | Required | Default | Production Hint |
|----------|----------|---------|----------------|
| `DATABASE_URL` | ✅ | — | Use SSL connection string |
| `REDIS_URL` | ✅ | `redis://redis:6379/0` | Internal Docker DNS |
| `SECRET_KEY` | ✅ | — | `openssl rand -hex 64` |
| `JWT_ALGORITHM` | ❌ | `HS256` | Keep default |
| `JWT_EXPIRATION_MINUTES` | ❌ | `30` | 15–60 min recommended |
| `STORAGE_PROVIDER` | ❌ | `supabase` | Must be configured |
| `SUPABASE_URL` | conditional | — | Required if `supabase` |
| `SUPABASE_SERVICE_KEY` | conditional | — | Service key, not anon key |
| `SUPABASE_STORAGE_BUCKET` | ❌ | `reports` | — |
| `MAX_UPLOAD_SIZE` | ❌ | `52428800` | 50 MB |
| `ALLOWED_EXTENSIONS` | ❌ | `.pdf,.docx` | Comma-separated |
| `CORS_ORIGINS` | ✅ | — | JSON array of origins |
| `LOG_LEVEL` | ❌ | `INFO` | `INFO` or `WARNING` in prod |
| `DEBUG` | ❌ | `false` | Must be `false` in prod |
| `APP_ENV` | ❌ | `production` | Must be `production` |

---

## Troubleshooting

### Container keeps restarting

```bash
docker compose -f docker-compose.prod.yml logs backend
```
Common causes: database unreachable, SECRET_KEY missing, port already in use.

### Database connection refused

Check PostgreSQL is healthy and the connection string is correct:
```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs postgres
```

### Out of memory

Increase Docker memory limits or reduce `MAX_UPLOAD_SIZE`:
```bash
# Check current usage
docker stats

# Edit docker-compose.prod.yml and increase deploy.resources.limits.memory
```

### File upload fails

Check disk space and storage provider configuration:
```bash
df -h
docker compose -f docker-compose.prod.yml logs backend | grep -i storage
```
