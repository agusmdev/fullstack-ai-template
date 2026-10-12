.PHONY: help up up-d down down-v logs logs-backend logs-db restart restart-backend build rebuild rebuild-backend ps clean \
	backend-shell backend-dev backend-install backend-format backend-lint backend-lint-fix backend-check backend-typecheck \
	frontend-shell frontend-dev frontend-install frontend-build frontend-lint frontend-lint-fix frontend-format frontend-format-check frontend-typecheck \
	migrate migrate-create migrate-rollback migrate-history migrate-current db-shell db-reset \
	test test-backend test-backend-cov test-e2e lint lint-fix format typecheck check ci quality \
	pre-commit-install pre-commit-run setup check-ports start stop restart-all dev dev-backend dev-fresh api-docs api-health

# ty is not a project dependency: run a pinned release with uvx.
# Supply-chain policy: a release at least 7 days old (0.0.84 = 2026-09-24).
TY_VERSION := 0.0.84

# Default target
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# Docker Compose Commands
# ============================================================================

up: ## Start all services (docker compose up)
	docker compose up

up-d: ## Start all services in detached mode
	docker compose up -d

down: ## Stop all services
	docker compose down

down-v: ## Stop all services and remove volumes (resets database)
	docker compose down -v

logs: ## View logs from all services
	docker compose logs -f

logs-backend: ## View backend logs only
	docker compose logs -f backend

logs-db: ## View database logs only
	docker compose logs -f db

restart: ## Restart all services
	docker compose restart

restart-backend: ## Restart backend service only
	docker compose restart backend

build: ## Build all images without starting them
	docker compose build

rebuild: ## Rebuild and start all services
	docker compose up --build

rebuild-backend: ## Rebuild and start backend service only
	docker compose up --build backend

ps: ## Show running services
	docker compose ps

clean: ## Stop services and remove this project's containers, networks and volumes
	docker compose down -v --remove-orphans

# ============================================================================
# Backend Development Commands
# ============================================================================

backend-shell: ## Open a shell in the backend container
	docker compose exec backend /bin/sh

backend-dev: ## Start backend development server locally (requires uv)
	cd backend && uv sync && uv run uvicorn --factory app.main:create_app --reload --host 0.0.0.0 --port 9095

backend-install: ## Install backend dependencies locally (requires uv)
	cd backend && uv sync

backend-format: ## Format backend code with ruff
	cd backend && uv run ruff format .

backend-lint: ## Lint backend code with ruff
	cd backend && uv run ruff check .

backend-lint-fix: ## Lint and auto-fix backend code
	cd backend && uv run ruff check . --fix

backend-check: ## Check backend lint + format without changing files (what CI runs)
	cd backend && uv run ruff check . && uv run ruff format --check .

backend-typecheck: ## Type-check the backend with ty (advisory: known diagnostics, not run in CI)
	cd backend && uvx ty@$(TY_VERSION) check app

# ============================================================================
# Frontend Development Commands
# ============================================================================

frontend-shell: ## Open a shell in the frontend container
	docker compose exec frontend /bin/sh

frontend-dev: ## Start frontend development server locally (requires bun)
	cd frontend && bun install && bun run dev

frontend-install: ## Install frontend dependencies locally (requires bun)
	cd frontend && bun install --frozen-lockfile

frontend-build: ## Build the frontend bundle locally
	cd frontend && bun run build

frontend-lint: ## Lint frontend code (ESLint, includes the e2e/ no-mock rules)
	cd frontend && bun run lint

frontend-lint-fix: ## Lint and auto-fix frontend code
	cd frontend && bun run lint:fix

frontend-format: ## Format frontend code with prettier
	cd frontend && bun run format

frontend-format-check: ## Check frontend formatting without changing files
	cd frontend && bun run format:check

frontend-typecheck: ## Type-check the frontend (tsc --noEmit)
	cd frontend && bun run typecheck

# ============================================================================
# Database & Migration Commands
# ============================================================================

migrate: ## Apply all pending database migrations
	cd backend && uv run alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create message="your message")
	@if [ -z "$(message)" ]; then \
		echo "Error: message parameter is required"; \
		echo "Usage: make migrate-create message=\"your migration description\""; \
		exit 1; \
	fi
	cd backend && uv run alembic revision --autogenerate -m "$(message)"

migrate-rollback: ## Rollback last migration
	cd backend && uv run alembic downgrade -1

migrate-history: ## View migration history
	cd backend && uv run alembic history

migrate-current: ## Show current migration version
	cd backend && uv run alembic current

db-shell: ## Open PostgreSQL shell in database container
	docker compose exec db sh -c 'exec psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

db-reset: ## Wipe the database (remove volumes, start db only, migrate)
	docker compose down -v
	docker compose up -d --wait db
	$(MAKE) migrate

# ============================================================================
# Testing & Quality Commands
# ============================================================================

# All tests are end-to-end against the real stack (no mocks, no unit tests).
# Both suites start their own Postgres in Docker and never touch the dev stack.

test: ## Run both end-to-end suites (backend API, then full-stack browser)
	$(MAKE) test-backend
	$(MAKE) test-e2e

test-backend: ## Backend e2e suite: Postgres container + migrations + live API (needs Docker)
	cd backend && uv run pytest

test-backend-cov: ## Backend e2e suite with an app/ coverage report (htmlcov/)
	cd backend && uv run pytest --cov=app --cov-report=html --cov-report=term

test-e2e: ## Full-stack e2e: Postgres + backend + Vite + Playwright (needs Docker, uv, bun, chromium)
	cd frontend && bun run test:e2e

lint: ## Run all linters
	$(MAKE) backend-lint
	$(MAKE) frontend-lint

lint-fix: ## Run linters with auto-fix
	$(MAKE) backend-lint-fix
	$(MAKE) frontend-lint-fix

format: ## Format all code
	$(MAKE) backend-format
	$(MAKE) frontend-format

typecheck: ## Run blocking type checks (frontend tsc; backend ty is advisory: make backend-typecheck)
	$(MAKE) frontend-typecheck

check: ## Run every static check CI runs, without changing files
	$(MAKE) backend-check
	$(MAKE) frontend-lint
	$(MAKE) frontend-format-check
	$(MAKE) frontend-build
	$(MAKE) frontend-typecheck

ci: ## Run what CI runs: static checks, then both e2e suites
	$(MAKE) check
	$(MAKE) test

quality: ## Format, lint and type-check (changes files)
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) typecheck

pre-commit-install: ## Install the git pre-commit hooks (.pre-commit-config.yaml; needs a git repo)
	cd backend && uv run pre-commit install --config ../.pre-commit-config.yaml

pre-commit-run: ## Run the pre-commit hooks on all files
	cd backend && uv run pre-commit run --all-files --config ../.pre-commit-config.yaml

# ============================================================================
# Environment & Setup Commands
# ============================================================================

setup: ## Initial setup (copy .env.example files, install deps)
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env; \
	else \
		echo ".env already exists, skipping..."; \
	fi
	@if [ ! -f backend/.env ]; then \
		echo "Creating backend/.env from backend/.env.example..."; \
		cp backend/.env.example backend/.env; \
	else \
		echo "backend/.env already exists, skipping..."; \
	fi
	$(MAKE) backend-install
	$(MAKE) frontend-install

check-ports: ## Check if default ports are available
	@echo "Checking default ports..."
	@echo "Backend (9095):"
	@lsof -i :9095 || echo "  ✓ Available"
	@echo "Frontend (3000):"
	@lsof -i :3000 || echo "  ✓ Available"
	@echo "Database (5432):"
	@lsof -i :5432 || echo "  ✓ Available"

# ============================================================================
# Quick Start Commands
# ============================================================================

start: ## Quick start all services (up-d + logs)
	$(MAKE) up-d
	@echo "Services started in background. View logs with: make logs"
	@echo ""
	@echo "Access the application:"
	@echo "  Backend API: http://localhost:9095"
	@echo "  API Docs:    http://localhost:9095/docs"
	@echo "  Frontend:    http://localhost:3000"

stop: ## Quick stop all services
	$(MAKE) down

restart-all: ## Quick restart all services
	$(MAKE) down
	$(MAKE) up-d

# ============================================================================
# Development Workflow Commands
# ============================================================================

dev: ## Start development environment (all services + logs)
	$(MAKE) up

dev-backend: ## Start only backend and database
	docker compose up backend db

dev-fresh: ## Fresh start (clean, setup, start; the backend container migrates on boot)
	$(MAKE) clean
	$(MAKE) setup
	$(MAKE) start

# ============================================================================
# API Testing Commands
# ============================================================================

api-docs: ## Open API documentation in browser
	@echo "Opening API docs..."
	@command -v open >/dev/null 2>&1 && open http://localhost:9095/docs || echo "Visit: http://localhost:9095/docs"

api-health: ## Check API health endpoint
	@curl -s http://localhost:9095/health || echo "Backend is not running"
