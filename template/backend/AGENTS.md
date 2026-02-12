# AGENTS.md — Backend Development Guide

## Commands
- **Run all tests:** `uv run pytest tests/`
- **Run single test:** `uv run pytest tests/path/to/test.py::test_function_name -v`
- **Run unit tests:** `uv run pytest tests/unit -v`
- **Lint & format:** `uv run ruff check app --fix && uv run ruff format app`
- **Run app:** `uv run uvicorn app.main:app --reload`
- **Generate migration:** `uv run alembic revision --autogenerate -m "description"`
- **Apply migrations:** `uv run alembic upgrade head`

## Tech Stack
- **Language:** Python 3.12+
- **Framework:** FastAPI (async)
- **ORM:** SQLAlchemy 2 (`Mapped[]`, `mapped_column`)
- **Validation:** Pydantic 2
- **Migrations:** Alembic
- **Linting:** Ruff (line-length=100, isort)
- **Logging:** Loguru with structured wide events
- **Auth:** Session-based, argon2 password hashing

## Architecture

**Pattern:** Router → Service → Repository (strict layering)

- **Routers:** HTTP endpoints only. NO business logic. Inject service via `Depends(get_*_service)`.
- **Services:** ALL business logic. Inherit `BaseService[T]` from `app/services/base_crud_service.py`.
- **Repositories:** Data access only. Inherit `SQLAlchemyRepository[T]` from `app/repositories/sql_repository.py`. Uses INSERT...RETURNING, ON CONFLICT.
- **Modules:** Self-contained in `app/modules/{name}/` with: `models.py`, `schemas.py`, `repository.py`, `service.py`, `routers.py`, `filters.py`, `dependencies.py`

```
app/
├── main.py              # App factory, CORS, middleware, Sentry
├── routers.py           # Central router registration
├── core/                # Config, permissions, logging, base schemas
├── database/            # Base model, engine, session, mixins
├── repositories/        # BaseRepository, SQLAlchemyRepository, QueryBuilder
├── services/            # BaseService (generic CRUD)
├── dependencies/        # Engine singleton, session factory, get_repository()
├── middlewares/          # RequestContextMiddleware
├── user/                # User + Auth module (models, service, routers)
│   └── auth/            # Session auth (register, login, logout, me)
└── modules/             # Feature modules (e.g., items/)
```

## Dependency Injection

Uses **FastAPI's native `Depends()`** with factory functions. No DI container.

```python
# app/dependencies/__init__.py provides:
get_repository(RepoType)  # Generic factory → returns Depends()-compatible callable

# Each module has dependencies.py:
def get_item_service(
    repo: ItemRepository = Depends(get_repository(ItemRepository)),
) -> ItemService:
    return ItemService(repo=repo)

# Router uses:
async def list_items(service: ItemService = Depends(get_item_service)):
    ...
```

## Auth

- **Guard dependency:** `Depends(AuthenticatedUser.current_user_id)` on protected routers
- **Get user ID:** `user_id: uuid.UUID = Depends(AuthenticatedUser.current_user_id)`
- **Get email:** `email: str = Depends(AuthenticatedUser.current_user_email)`
- Session-based with Bearer token transport, argon2 hashing, DB-stored sessions

## Error Handling

- Custom exceptions inherit `HTTPExceptionMixin` with class attrs: `status_code`, `detail`, `error_code`
- Repository exceptions auto-parsed from SQLAlchemy `IntegrityError`:
  - `NotFoundError` (404) — entity not found
  - `DuplicateError` (400) — unique constraint violation
  - `ReferencedError` (400) — foreign key constraint violation

## Logging

Wide event / canonical log lines pattern via `WideEventMiddleware`:
- One structured log per request with method, path, duration, status, client IP, errors
- In handlers, use helpers: `log_action("create")`, `log_entity("item", item_id)`, `log_custom(key=value)`
- Sensitive data auto-redacted (passwords, tokens, secrets, API keys)

## Code Style
- **Formatting:** Ruff. Imports: stdlib → third-party → local (`app.`)
- **Naming:** snake_case (functions/vars), PascalCase (classes), SCREAMING_SNAKE_CASE (constants)
- **Types:** Type hints everywhere. `@partial_model` for update schemas. SQLAlchemy models inherit `Base` + `TimestampMixin`
- **Git:** Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`)

## New Entities

Create in `app/modules/` following the items module pattern. Use `/skill:add-backend-entity` for step-by-step guidance.

**Quick checklist:** models.py → schemas.py → repository.py → service.py → filters.py → dependencies.py → routers.py → register in `app/routers.py` → generate migration
