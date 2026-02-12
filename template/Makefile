.PHONY: help up down logs restart clean rebuild test lint format migrate migrate-create migrate-rollback db-reset backend-dev backend-shell frontend-dev check-ports

# Default target
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# Docker Compose Commands
# ============================================================================

up: ## Start all services (docker-compose up)
	docker-compose up

up-d: ## Start all services in detached mode
	docker-compose up -d

down: ## Stop all services
	docker-compose down

down-v: ## Stop all services and remove volumes (resets database)
	docker-compose down -v

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs only
	docker-compose logs -f backend

logs-db: ## View database logs only
	docker-compose logs -f db

restart: ## Restart all services
	docker-compose restart

restart-backend: ## Restart backend service only
	docker-compose restart backend

rebuild: ## Rebuild and start all services
	docker-compose up --build

rebuild-backend: ## Rebuild and start backend service only
	docker-compose up --build backend

ps: ## Show running services
	docker-compose ps

clean: ## Stop services and clean up containers, networks, and volumes
	docker-compose down -v
	docker system prune -f

# ============================================================================
# Backend Development Commands
# ============================================================================

backend-shell: ## Open a shell in the backend container
	docker-compose exec backend /bin/sh

backend-dev: ## Start backend development server locally (requires uv)
	cd backend && uv sync && uv run uvicorn src.app:app --reload --host 0.0.0.0 --port 9095

backend-install: ## Install backend dependencies locally (requires uv)
	cd backend && uv sync

backend-test: ## Run backend tests locally
	cd backend && uv run pytest

backend-test-cov: ## Run backend tests with coverage report
	cd backend && uv run pytest --cov=src --cov-report=html

backend-format: ## Format backend code with ruff
	cd backend && uv run ruff format .

backend-lint: ## Lint backend code with ruff
	cd backend && uv run ruff check .

backend-lint-fix: ## Lint and auto-fix backend code
	cd backend && uv run ruff check . --fix

backend-typecheck: ## Run type checking on backend code
	cd backend && uv run ty check

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
	docker-compose exec db psql -U app -d app

db-reset: ## Reset database (stop, remove volumes, restart, migrate)
	docker-compose down -v
	docker-compose up -d db
	sleep 3
	$(MAKE) migrate

# ============================================================================
# Testing & Quality Commands
# ============================================================================

test: ## Run all backend tests
	$(MAKE) backend-test

test-cov: ## Run tests with coverage report
	$(MAKE) backend-test-cov

lint: ## Run all linters
	$(MAKE) backend-lint

lint-fix: ## Run linters with auto-fix
	$(MAKE) backend-lint-fix

format: ## Format all code
	$(MAKE) backend-format

typecheck: ## Run type checking
	$(MAKE) backend-typecheck

quality: ## Run all quality checks (format, lint, typecheck)
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) typecheck

# ============================================================================
# Environment & Setup Commands
# ============================================================================

setup: ## Initial setup (copy .env.example, install deps)
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

check-ports: ## Check if default ports are available
	@echo "Checking default ports..."
	@echo "Backend (9095):"
	@lsof -i :9095 || echo "  ✓ Available"
	@echo "Frontend (3150):"
	@lsof -i :3150 || echo "  ✓ Available"
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
	@echo "  Frontend:    http://localhost:3150"

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
	docker-compose up backend db

dev-fresh: ## Fresh start (clean, setup, start)
	$(MAKE) clean
	$(MAKE) setup
	$(MAKE) start
	$(MAKE) migrate

# ============================================================================
# API Testing Commands
# ============================================================================

api-docs: ## Open API documentation in browser
	@echo "Opening API docs..."
	@command -v open >/dev/null 2>&1 && open http://localhost:9095/docs || echo "Visit: http://localhost:9095/docs"

api-health: ## Check API health endpoint
	@curl -s http://localhost:9095/health || echo "Backend is not running"
