.PHONY: setup dev build lint format test clean docker-build docker-up

# Default target
all: setup lint test

## Environment & Dependencies
setup:
	@echo "Setting up development environment..."
	@bash scripts/setup.sh

## Development Servers
dev:
	@echo "Starting development servers..."
	@bash scripts/dev.sh

## Build
build:
	@echo "Building all packages..."
	@bash scripts/build.sh

## Linting
lint:
	@echo "Running linters..."
	@bash scripts/lint.sh

## Formatting
format:
	@echo "Running formatters..."
	@bash scripts/format.sh

## Testing
test:
	@echo "Running tests..."
	@bash scripts/test.sh

## Cleanup
clean:
	@echo "Cleaning caches and build artifacts..."
	@rm -rf .pytest_cache .mypy_cache .ruff_cache __pycache__
	@rm -rf apps/backend/__pycache__ packages/core/__pycache__ packages/shared/__pycache__
	@rm -rf apps/backend/.pytest_cache packages/core/.pytest_cache packages/shared/.pytest_cache
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .next node_modules/.cache
	@echo "Clean complete."

## Docker (Development)
docker-up:
	@echo "Starting development infrastructure..."
	@docker compose -f docker-compose.dev.yml up -d

docker-down:
	@echo "Stopping development infrastructure..."
	@docker compose -f docker-compose.dev.yml down

docker-reset:
	@echo "Resetting development infrastructure..."
	@docker compose -f docker-compose.dev.yml down -v

## Docker (Production)
deploy:
	@echo "Deploying production stack..."
	@bash scripts/deploy.sh

prod-up:
	@echo "Starting production stack..."
	@docker compose -f docker-compose.prod.yml up -d --build

prod-down:
	@echo "Stopping production stack..."
	@docker compose -f docker-compose.prod.yml down

prod-logs:
	@echo "Tailing production logs..."
	@docker compose -f docker-compose.prod.yml logs -f
