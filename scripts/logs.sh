#!/usr/bin/env bash
set -euo pipefail

SERVICE="${1:-}"

DEFAULT_COMPOSE="docker-compose.yml"
COMPOSE_FILE="${DEFAULT_COMPOSE}"
SERVICE="${1:-}"

case "$SERVICE" in
    --prod)
        COMPOSE_FILE="docker-compose.prod.yml"
        shift
        SERVICE="${1:-}"
        ;;
    --dev|--*)
        SERVICE=""
        ;;
esac

if [ -n "$SERVICE" ]; then
    docker compose -f "$COMPOSE_FILE" logs -f "$SERVICE"
else
    docker compose -f "$COMPOSE_FILE" logs -f
fi
