#!/usr/bin/env bash
set -euo pipefail

echo "=== Running formatters ==="

PYTHON_DIRS="apps/backend packages/core packages/shared"

# ruff format
echo "Running ruff format..."
ruff format $PYTHON_DIRS
echo "  ruff format complete."

# npm format
if [ -d "apps/frontend" ]; then
    echo "Running npm format..."
    cd apps/frontend && npm run format && cd ../..
elif [ -f "package.json" ]; then
    echo "Running npm format..."
    npm run format
fi

echo "=== Formatting complete ==="
