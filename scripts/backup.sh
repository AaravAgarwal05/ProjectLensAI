#!/usr/bin/env bash
# ProjectLens AI — PostgreSQL backup.
#
# Dumps the production database via pg_dump (run inside the postgres
# container) to ./backups/projectlens_<date>.dump, keeping the last
# BACKUP_KEEP (default 14) dumps. Restore with:
#   docker compose -f docker-compose.prod.yml exec -T postgres \
#     pg_restore -U $POSTGRES_USER -d $POSTGRES_DB \
#     < ./backups/projectlens_<date>.dump
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
BACKUP_KEEP="${BACKUP_KEEP:-14}"

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "✗ $COMPOSE_FILE not found — run from the repo root." >&2
    exit 1
fi

# Pull DB credentials from .env.production (loaded by compose).
set -a
source .env.production 2>/dev/null || true
set +a

POSTGRES_USER="${POSTGRES_USER:?POSTGRES_USER must be set (see .env.production)}"
POSTGRES_DB="${POSTGRES_DB:-projectlens}"

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
DEST="$BACKUP_DIR/projectlens_$STAMP.dump"

echo "→ Dumping $POSTGRES_DB to $DEST ..."
docker compose -f "$COMPOSE_FILE" exec -T postgres \
    pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB" > "$DEST"
echo "✓ Backup written: $DEST ($(du -h "$DEST" | cut -f1))"

# Prune old backups.
COUNT=$(ls -1 "$BACKUP_DIR"/projectlens_*.dump 2>/dev/null | wc -l)
if [ "$COUNT" -gt "$BACKUP_KEEP" ]; then
    ls -1t "$BACKUP_DIR"/projectlens_*.dump | tail -n +$((BACKUP_KEEP + 1)) | xargs rm -f
    echo "→ Pruned old backups, keeping the last $BACKUP_KEEP."
fi
