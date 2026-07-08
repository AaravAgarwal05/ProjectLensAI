#!/usr/bin/env bash
set -euo pipefail

echo "=== ProjectLens AI Setup ==="

# Copy environment file if not present
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Created .env from .env.example"
    else
        echo "Warning: .env.example not found, skipping"
    fi
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -e ".[dev]" 2>/dev/null || pip install -e "."
pip install -e "packages/core" 2>/dev/null || true
pip install -e "packages/shared" 2>/dev/null || true

# Check for Node.js and install frontend dependencies
if command -v npm &> /dev/null; then
    if [ -d "apps/frontend" ]; then
        echo "Installing frontend dependencies..."
        cd apps/frontend && npm install && cd ../..
    elif [ -f "package.json" ]; then
        echo "Installing Node dependencies..."
        npm install
    fi
else
    echo "Warning: npm not found, skipping frontend setup"
fi

# Set up pre-commit hooks
if command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit hooks..."
    pre-commit install
else
    echo "Warning: pre-commit not found, skipping hook installation"
fi

echo "=== Setup complete ==="
