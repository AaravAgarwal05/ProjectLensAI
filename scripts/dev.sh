#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     ProjectLens AI — Dev Environment    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"

# Ensure apps/backend/.env.local exists (read by pydantic-settings for native dev)
if [ ! -f "apps/backend/.env.local" ]; then
    if [ -f "apps/backend/.env.example" ]; then
        echo -e "${YELLOW}⚠ apps/backend/.env.local not found — copying from apps/backend/.env.example${NC}"
        cp apps/backend/.env.example apps/backend/.env.local
    else
        echo -e "${RED}✗ apps/backend/.env.example not found — create apps/backend/.env.local manually${NC}"
        exit 1
    fi
fi

# Also ensure root .env.local exists (used by Docker compose as fallback)
if [ ! -f ".env.local" ] && [ -f "config/.env.local.example" ]; then
    cp config/.env.local.example .env.local
fi

# Start infrastructure only (backend/frontend run natively for hot-reload)
echo -e "${YELLOW}Starting Docker infrastructure (PostgreSQL, ChromaDB, Redis)...${NC}"
docker compose -f docker-compose.yml up -d postgres chroma redis

# Wait for PostgreSQL
echo -e "${YELLOW}Waiting for PostgreSQL to be healthy...${NC}"
until docker compose -f docker-compose.yml exec -T postgres pg_isready -U postgres 2>/dev/null; do
    sleep 2
done
echo -e "${GREEN}✓ PostgreSQL is ready${NC}"

# Wait for Redis
echo -e "${YELLOW}Waiting for Redis to be healthy...${NC}"
until docker compose -f docker-compose.yml exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; do
    sleep 1
done
echo -e "${GREEN}✓ Redis is ready${NC}"

# Wait for ChromaDB
echo -e "${YELLOW}Waiting for ChromaDB to be healthy...${NC}"
until curl -s http://localhost:8001/api/v2/heartbeat 2>/dev/null | grep -q nanosecond; do
    sleep 2
done
echo -e "${GREEN}✓ ChromaDB is ready${NC}"

# Run migrations
if [ -d "apps/backend/alembic" ]; then
    echo -e "${YELLOW}Running database migrations...${NC}"
    cd apps/backend && uv run alembic upgrade head && cd ../.. \
        && echo -e "${GREEN}✓ Migrations applied${NC}" \
        || echo -e "${YELLOW}⚠ No migrations to apply${NC}"
fi

# Start backend
echo -e "${YELLOW}Starting backend (uvicorn)...${NC}"
cd apps/backend && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ../..

# Start frontend
if [ -d "apps/frontend" ]; then
    echo -e "${YELLOW}Starting frontend (Next.js)...${NC}"
    cd apps/frontend && npm run dev &
    FRONTEND_PID=$!
    cd ../..
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         All services are running!        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo -e "  ${BLUE}PostgreSQL:${NC}  postgresql://postgres:postgres@localhost:5432/projectlens"
echo -e "  ${BLUE}ChromaDB:${NC}    http://localhost:8001"
echo -e "  ${BLUE}Redis:${NC}       redis://localhost:6379"
echo -e "  ${BLUE}Backend:${NC}     http://localhost:8000"
echo -e "  ${BLUE}Frontend:${NC}    http://localhost:3000"
echo -e "  ${BLUE}API Docs:${NC}    http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers.${NC}"

cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    kill "${BACKEND_PID:-}" "${FRONTEND_PID:-}" 2>/dev/null || true
    wait 2>/dev/null || true
    echo -e "${GREEN}✓ Services stopped${NC}"
}
trap cleanup SIGINT SIGTERM EXIT

wait
