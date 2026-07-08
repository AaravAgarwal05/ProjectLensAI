#!/usr/bin/env bash
set -euo pipefail

echo "=== Building ProjectLens AI ==="

# Build backend
echo "Building backend..."
pip install -e "apps/backend" 2>/dev/null || pip install -e .

# Build shared packages
echo "Building shared packages..."
for pkg in packages/core packages/shared; do
    if [ -d "$pkg" ]; then
        echo "  Building $pkg..."
        pip install -e "$pkg" 2>/dev/null || true
    fi
done

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
