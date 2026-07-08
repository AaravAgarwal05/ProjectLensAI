#!/usr/bin/env bash
set -euo pipefail

echo "=== Running tests ==="

# Python tests
echo "Running pytest..."
python -m pytest -v --tb=short --strict-markers
echo "  pytest passed."

# Node tests
if [ -d "apps/frontend" ]; then
    echo "Running npm test..."
    cd apps/frontend && npm test && cd ../..
elif [ -f "package.json" ]; then
    echo "Running npm test..."
    npm test
fi

echo "=== All tests passed ==="
