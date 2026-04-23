# AGENTS.md

## Build/Test/Lint Commands
- **Run all tests:** `uv run pytest tests/`
- **Run single test:** `uv run pytest tests/unit/stmt_generator/test_statement_generator.py::test_function_name -v`
- **Run unit tests:** `uv run pytest tests/unit -v`
- **Lint & format:** `uv run ruff check app --fix && uv run ruff format app`
- **Type check:** `uvx ty check`
- **Run app:** `uv run uvicorn app.main:app --reload`
- **Generate migration:** `uv run alembic revision --autogenerate -m "description"`

## Code Style Guidelines
- **Python 3.12+**, FastAPI, SQLAlchemy 2 (`Mapped[]`, `mapped_column`), Pydantic 2
- **Formatting:** Ruff (line-length=100, isort). Imports: stdlib → third-party → local (`app.`)
- **Architecture:** Repository → Service → Router. Routers: NO business logic, delegate to services. Services: ALL business logic. Repos: use base `SQLAlchemyRepository` methods
- **Naming:** snake_case (functions/vars), PascalCase (classes), SCREAMING_SNAKE_CASE (constants)
- **Types:** Type hints everywhere. Pydantic schemas use `@partial_model` for updates. SQLAlchemy models inherit `Base` + `TimestampMixin`
- **Errors:** Inherit `HTTPExceptionMixin` with `status_code`, `detail`, `error_code` class attributes
- **Logging:** `loguru.logger` (debug, info, warning, error)
- **DI:** Services created via `get_*_service()` factory functions in `{module}/dependencies.py`. Injected into routers via FastAPI `Depends()`. See `app/user/dependencies.py` and `app/modules/items/dependencies.py` for examples.
- **Git:** Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`)
- **New entities:** Create in `app/modules/` with: models.py, schemas.py, repository.py, service.py, routers.py, filters.py (see docs/02-adding-new-entity.md)

## Package `__init__.py` Convention
- Packages with a **public API** (re-exported symbols): define `__all__` and list exports (see `app/repositories/__init__.py`, `app/modules/items/__init__.py`).
- Packages that are **internal namespaces** with no re-exports: empty `__init__.py` (one-line docstring is acceptable).
- **Never omit `__init__.py`** — missing init files cause inconsistent import behavior. Every package directory must have one.
- Auth boundary: domain modules import from `app.user.auth` (the package), not from `app.user.auth.permissions` directly.

## Error Boundary Strategy
Consistent error handling across layers:
- **Services/repositories:** raise domain exceptions (`NotFoundError`, `AuthenticationError`, etc.) with `from original_exc` to preserve context.
- **Routers:** do NOT catch exceptions — let them propagate to FastAPI exception handlers and middleware (which logs them). Exception: redirect-based OAuth endpoints may handle specific known exceptions at the router level.
- **External I/O (HTTP clients, OAuth):** catch protocol-level exceptions and wrap in domain exceptions with `from err`.
- **Never use `raise ... from None`** — always preserve original exception context for debugging.
