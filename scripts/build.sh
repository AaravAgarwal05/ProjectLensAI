#!/usr/bin/env bash
set -euo pipefail

echo "=== Building ProjectLens AI ==="

# Build backend + shared packages via uv
echo "Building backend..."
cd apps/backend && uv sync --extra dev && cd ../..

# Build frontend
if [ -d "apps/frontend" ]; then
    echo "Building frontend..."
    cd apps/frontend && npm run build && cd ../..
elif [ -f "package.json" ]; then
    echo "Building frontend..."
    npm run build
else
    echo "Warning: No frontend found, skipping"
fi

echo "=== Build complete ==="
