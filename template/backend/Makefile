.PHONY: help install clean lint format lint-all check run test test-cov migrate migrate-new migrate-history migrate-down pre-commit pre-commit-all venv

# Default target
help:
	@echo "Available commands:"
	@echo "  make install          - Install dependencies and set up the environment"
	@echo "  make clean            - Remove temporary files and caches"
	@echo "  make lint             - Run ruff linter with auto-fix"
	@echo "  make format           - Run ruff formatter"
	@echo "  make lint-all         - Run lint and format"
	@echo "  make check            - Check lint and format without changing files (CI)"
	@echo "  make run              - Run the FastAPI application on port 9095"
	@echo "  make test             - Run the end-to-end suite (needs Docker)"
	@echo "  make test-cov         - Run the end-to-end suite with an app coverage report"
	@echo "  make migrate          - Apply database migrations"
	@echo "  make migrate-new      - Create a new migration (usage: make migrate-new msg='description')"
	@echo "  make migrate-history  - Show migration history"
	@echo "  make migrate-down     - Downgrade migration by one"
	@echo "  make venv             - Activate virtual environment (source this)"
	@echo "  make pre-commit       - Install the project's git hooks (../.pre-commit-config.yaml)"
	@echo "  make pre-commit-all   - Run the project's git hooks on all files"

# Install dependencies and set up environment
install:
	@echo "Setting up virtual environment..."
	uv sync
	@echo "Installing pre-commit hooks..."
	$(MAKE) pre-commit
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
	uv run ruff check . --fix

# Run ruff formatter
format:
	@echo "Running ruff formatter..."
	uv run ruff format .

# Run both lint and format
lint-all: lint format

# Check lint and format without changing files (what CI runs)
check:
	uv run ruff check .
	uv run ruff format --check .

# Run the FastAPI application
run:
	uv run uvicorn --factory app.main:create_app --reload --port 9095

# Run the end-to-end suite: real Postgres (Docker) + migrations + live server
test:
	uv run pytest

# Same, with a coverage report of app/ (the server process is measured too)
test-cov:
	uv run pytest --cov=app --cov-report=html --cov-report=term
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

# The project has one pre-commit config, at the project root (backend ruff,
# frontend eslint + prettier, no-mock guards). pre-commit comes from this venv.
PRE_COMMIT_CONFIG := ../.pre-commit-config.yaml

# Install pre-commit hooks (needs a git repository)
pre-commit:
	uv run pre-commit install --config $(PRE_COMMIT_CONFIG)

# Run pre-commit on all files of the project
pre-commit-all:
	uv run pre-commit run --all-files --config $(PRE_COMMIT_CONFIG)

# Activate virtual environment (print instructions)
venv:
	@echo "To activate the virtual environment, run:"
	@echo "  source .venv/bin/activate"
	@echo ""
	@echo "To also load .env variables:"
	@echo "  source .venv/bin/activate && set -o allexport && source .env && set +o allexport"
