---
name: fastapi-project-setup
description: Initialize FastAPI project with uv, pyproject.toml, ruff configuration, and environment files
---

# FastAPI Project Setup

## Overview

This skill covers initializing a new FastAPI project with uv package manager, proper project configuration, and tooling setup.

## Step 1: Initialize Project with uv

```bash
uv init
```

## Step 2: Create pyproject.toml

```toml
[project]
name = "your-project-name"
version = "0.1.0"
description = "FastAPI backend application"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
    "sqlalchemy[asyncio]>=2.0.36",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "fastapi-pagination>=0.12.33",
    "fastapi-filter>=2.0.0",
    "python-json-logger>=3.2.1",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.8.0",
    "pytest>=8.3.0",
    "pytest-asyncio>=0.25.0",
    "httpx>=0.28.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/app"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
pythonpath = ["src"]
```

## Step 3: Create .python-version

```
3.12
```

## Step 4: Create ruff.toml

```toml
# Ruff configuration for FastAPI project

# Target Python 3.12
target-version = "py312"

# Line length
line-length = 100

# Exclude directories
exclude = [
    ".git",
    ".ruff_cache",
    ".venv",
    "venv",
    "__pycache__",
    "alembic/versions",
]

[lint]
# Enable rules
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
    "TCH",    # flake8-type-checking
    "PTH",    # flake8-use-pathlib
    "ERA",    # eradicate (commented-out code)
    "PL",     # Pylint
    "RUF",    # Ruff-specific rules
]

# Ignore specific rules
ignore = [
    "E501",   # line too long (handled by formatter)
    "B008",   # do not perform function calls in argument defaults (needed for Depends)
    "PLR0913", # too many arguments
    "PLR2004", # magic value comparison
]

# Allow autofix for all enabled rules
fixable = ["ALL"]
unfixable = []

[lint.per-file-ignores]
# Tests can have unused arguments (fixtures)
"tests/**/*.py" = ["ARG"]
# Alembic migrations
"alembic/**/*.py" = ["ERA"]

[lint.isort]
known-first-party = ["app"]
force-single-line = false
combine-as-imports = true

[format]
# Use double quotes for strings
quote-style = "double"

# Indent with spaces
indent-style = "space"

# Unix-style line endings
line-ending = "lf"

# Enable auto-formatting of docstrings
docstring-code-format = true
```

## Step 5: Create .env.example

```bash
# Application
APP_NAME=FastAPI App
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
DATABASE_ECHO=false
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Logging
LOG_LEVEL=INFO
LOG_JSON_FORMAT=true
```

## Step 6: Create config.py

Create `src/app/config.py`:

```python
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_name: str = "FastAPI App"
    debug: bool = False

    # Database
    database_url: PostgresDsn
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Logging
    log_level: str = "INFO"
    log_json_format: bool = True


settings = Settings()
```

## Step 7: Create Directory Structure

```bash
mkdir -p src/app/{core,common,middleware,api/v1}
mkdir -p tests/api/v1
mkdir -p alembic/versions
touch src/app/__init__.py
touch src/app/core/__init__.py
touch src/app/common/__init__.py
touch src/app/middleware/__init__.py
touch src/app/api/__init__.py
touch src/app/api/v1/__init__.py
touch tests/__init__.py
touch tests/api/__init__.py
touch tests/api/v1/__init__.py
touch alembic/versions/.gitkeep
```

## Step 8: Install Dependencies

```bash
uv sync
uv sync --dev
```

## Verification

After setup, verify:
1. `uv run python -c "import fastapi; print(fastapi.__version__)"` works
2. `uv run ruff check src/` runs without errors
3. `.env` file is created from `.env.example` with actual values

## Notes

- Always use `uv run` to execute commands within the virtual environment
- Never commit `.env` file, only `.env.example`
- Keep dependencies up to date with `uv lock --upgrade`
