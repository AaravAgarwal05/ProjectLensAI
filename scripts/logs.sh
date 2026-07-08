#!/usr/bin/env bash
set -euo pipefail

SERVICE="${1:-}"

if [ -n "$SERVICE" ]; then
    docker compose -f docker-compose.dev.yml logs -f "$SERVICE"
else
    docker compose -f docker-compose.dev.yml logs -f
fi
