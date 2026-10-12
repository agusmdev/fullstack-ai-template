.PHONY: help install clean lint format lint-all run test test-integration test-cov migrate migrate-new migrate-history migrate-down pre-commit pre-commit-all venv

# Default target
help:
	@echo "Available commands:"
	@echo "  make install          - Install dependencies and set up the environment"
	@echo "  make clean            - Remove temporary files and caches"
	@echo "  make lint             - Run ruff linter with auto-fix"
	@echo "  make format           - Run ruff formatter"
	@echo "  make lint-all         - Run lint and format"
	@echo "  make run              - Run the FastAPI application on port 9095"
	@echo "  make test             - Run all tests"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-cov         - Run tests with coverage report"
	@echo "  make migrate          - Apply database migrations"
	@echo "  make migrate-new      - Create a new migration (usage: make migrate-new msg='description')"
	@echo "  make migrate-history  - Show migration history"
	@echo "  make migrate-down     - Downgrade migration by one"
	@echo "  make venv             - Activate virtual environment (source this)"
	@echo "  make pre-commit       - Install pre-commit hooks"
	@echo "  make pre-commit-all   - Run pre-commit on all files"

# Install dependencies and set up environment
install:
	@echo "Setting up virtual environment..."
	uv sync
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install
	@echo "Installation complete!"

# Remove temporary files and caches
clean:
	@echo "Cleaning up temporary files..."
	rm -f .coverage.* .coverage coverage.xml report.xml
	rm -rf tests/coverage htmlcov
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "Cleanup complete!"

# Run ruff linter with auto-fix
lint:
	@echo "Running ruff linter..."
	uv run ruff check app --fix

# Run ruff formatter
format:
	@echo "Running ruff formatter..."
	uv run ruff format app

# Run both lint and format
lint-all: lint format

# Run the FastAPI application
run:
	uv run uvicorn --factory app.main:create_app --reload --port 9095

# Run all tests
test:
	uv run pytest tests/ -v

# Run integration tests only
test-integration:
	@echo "Running integration tests..."
	uv run pytest tests/integration -v

# Run tests with coverage
test-cov:
	uv run pytest tests/ --cov=app --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/"

# Apply database migrations
migrate:
	uv run alembic upgrade head

# Create a new migration
# Usage: make migrate-new msg="description"
migrate-new:
ifndef msg
	$(error msg is required. Usage: make migrate-new msg="description")
endif
	uv run alembic revision --autogenerate -m "$(msg)"

# Show migration history
migrate-history:
	uv run alembic history

# Downgrade migration by one
migrate-down:
	uv run alembic downgrade -1

# Install pre-commit hooks
pre-commit:
	uv run pre-commit install

# Run pre-commit on all files
pre-commit-all:
	uv run pre-commit run --all-files

# Activate virtual environment (print instructions)
venv:
	@echo "To activate the virtual environment, run:"
	@echo "  source .venv/bin/activate"
	@echo ""
	@echo "To also load .env variables:"
	@echo "  source .venv/bin/activate && set -o allexport && source .env && set +o allexport"
