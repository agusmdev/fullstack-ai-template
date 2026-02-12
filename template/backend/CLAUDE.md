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
- **DI:** `Inject[ServiceClass]` in constructors, `Injected(Service)` in routers, register in `app/dependency_registry.py`
- **Git:** Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`)
- **New entities:** Create in `app/modules/` with: models.py, schemas.py, repository.py, service.py, routers.py, filters.py (see docs/02-adding-new-entity.md)
