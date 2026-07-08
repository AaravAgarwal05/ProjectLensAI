#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${RED}╔══════════════════════════════════════════╗${NC}"
echo -e "${RED}║      FULL RESET — all data will be lost  ║${NC}"
echo -e "${RED}╚══════════════════════════════════════════╝${NC}"
read -p "Are you sure? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Cancelled.${NC}"
    exit 1
fi

echo -e "${YELLOW}Stopping containers and removing volumes...${NC}"
docker compose -f docker-compose.dev.yml down -v
echo -e "${GREEN}✓ Containers and volumes removed${NC}"

if [ -f ".env.local" ]; then
    echo -e "${YELLOW}Removing .env.local...${NC}"
    rm .env.local
    echo -e "${GREEN}✓ Removed${NC}"
fi

echo -e "${BLUE}Re-running development setup...${NC}"
exec ./scripts/dev.sh
