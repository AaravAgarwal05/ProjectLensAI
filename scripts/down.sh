#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

COMPOSE_FILE="docker-compose.dev.yml"
REMOVE_VOLUMES=false

# Parse args
for arg in "$@"; do
    case "$arg" in
        -v|--volumes) REMOVE_VOLUMES=true ;;
        --prod)       COMPOSE_FILE="docker-compose.prod.yml" ;;
    esac
done

echo -e "${YELLOW}Stopping services (${COMPOSE_FILE})...${NC}"

if [ "$REMOVE_VOLUMES" = true ]; then
    echo -e "${RED}Removing volumes (data will be lost!)...${NC}"
    docker compose -f "$COMPOSE_FILE" down -v
    echo -e "${GREEN}✓ Containers and volumes removed${NC}"
else
    docker compose -f "$COMPOSE_FILE" down
    echo -e "${GREEN}✓ Containers stopped${NC}"
    echo -e "${YELLOW}Tip: Use -v flag to also remove volumes${NC}"
fi
