#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    ProjectLens AI — Production Deploy   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"

# Check .env.production exists
if [ ! -f ".env.production" ]; then
    if [ -f ".env.production.example" ]; then
        echo -e "${RED}✗ .env.production not found${NC}"
        echo -e "${YELLOW}  Copy from template: cp .env.production.example .env.production${NC}"
        echo -e "${YELLOW}  Then edit .env.production with real values before deploying.${NC}"
        exit 1
    else
        echo -e "${RED}✗ .env.production.example not found — cannot deploy${NC}"
        exit 1
    fi
fi

# Check SECRET_KEY is not default
if grep -q "replace-with-openssl" .env.production 2>/dev/null || grep -q "change-this" .env.production 2>/dev/null; then
    echo -e "${RED}✗ SECRET_KEY still has default value in .env.production${NC}"
    echo -e "${YELLOW}  Generate a strong key: openssl rand -hex 64${NC}"
    exit 1
fi

echo -e "${YELLOW}Building and starting production services...${NC}"
docker compose -f docker-compose.prod.yml build --pull
docker compose -f docker-compose.prod.yml up -d

echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 5

# Check backend health
if curl -sf http://localhost/api/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
    echo -e "${YELLOW}  Run: docker compose -f docker-compose.prod.yml logs backend${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Production deployment done!       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo -e "  ${BLUE}Frontend:${NC}  http://localhost"
echo -e "  ${BLUE}Backend:${NC}   http://localhost/api"
echo -e "  ${BLUE}Health:${NC}    http://localhost/api/v1/health"
echo ""
echo -e "${YELLOW}Commands:${NC}"
echo -e "  Logs:    docker compose -f docker-compose.prod.yml logs -f"
echo -e "  Stop:    docker compose -f docker-compose.prod.yml down"
echo -e "  Update:  git pull && docker compose -f docker-compose.prod.yml up -d --build"
