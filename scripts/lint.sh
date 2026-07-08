#!/usr/bin/env bash
set -euo pipefail

echo "=== Running linters ==="

PYTHON_DIRS="apps/backend packages/core packages/shared"

# ruff
echo "Running ruff..."
ruff check $PYTHON_DIRS
echo "  ruff passed."

# mypy
echo "Running mypy..."
for dir in $PYTHON_DIRS; do
    src_dir="$dir/src"
    if [ -d "$src_dir" ]; then
        echo "  mypy: $src_dir"
        mypy "$src_dir"
    fi
done
echo "  mypy passed."

# npm lint
if [ -d "apps/frontend" ]; then
    echo "Running npm lint..."
    cd apps/frontend && npm run lint && cd ../..
elif [ -f "package.json" ]; then
    echo "Running npm lint..."
    npm run lint
fi

echo "=== All linters passed ==="
