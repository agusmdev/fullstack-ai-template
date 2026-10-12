# AGENTS.md — Backend Development Guide

## Commands
- **Run all tests:** `uv run pytest tests/`
- **Run single test:** `uv run pytest tests/path/to/test.py::test_function_name -v`
- **Run unit tests:** `uv run pytest tests/unit -v`
- **Lint & format:** `uv run ruff check app --fix && uv run ruff format app`
- **Type check:** `uvx ty check`
- **Run app:** `uv run uvicorn app.main:app --reload`
- **Generate migration:** `uv run alembic revision --autogenerate -m "description"`
- **Apply migrations:** `uv run alembic upgrade head`

## uv / PyPI Supply-Chain Policy

**Before adding any Python package** (`uv add`, `uv add --dev`, editing `pyproject.toml`), the agent MUST:

1. **Search the web** for the package's latest stable, non-vulnerable release — check the PyPI project page, the project's GitHub releases, and CVE advisories (PyPI's `osv.dev`, GitHub Security Advisories, Snyk, `pip-audit`).
2. **Verify** the chosen version is at least 7 days old and has no open critical/high CVEs. If the latest release is younger than 7 days, pick the most recent release that is ≥ 7 days old and note the choice in the commit message.
3. **Pin to the exact version** in `pyproject.toml` using `==`, never `>=` or `~=`. Example: `"fastapi==0.118.0"`, never `"fastapi>=0.115.0"`. Preserve extras: `"pydantic[email]==2.11.10"`.
4. **Run `uv lock`** to update `uv.lock`, then commit both `pyproject.toml` and `uv.lock` together so the resolved tree is locked in git.

**Adding a new dep:** `uv add 'pkg==X.Y.Z'` (always with `==X.Y.Z`, never bare `uv add pkg`).

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
- **Repositories:** Data access only. Inherit `SQLAlchemyRepository[T]` from `app/repositories/sql_repository.py` and use its base methods. Uses INSERT...RETURNING, ON CONFLICT.
- **Modules:** Self-contained in `app/modules/{name}/` with: `models.py`, `schemas.py`, `repository.py`, `service.py`, `routers.py`, `filters.py`, `dependencies.py`

```
app/
├── main.py              # App factory, CORS, middleware, Sentry
├── routers.py           # Central router registration
├── core/                # Config, logging, base schemas
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

- **Guard dependency (feature modules):** `Depends(require_current_user_id)`, imported from `app.user.auth` (see `app/modules/items/routers.py`)
- **Get user ID:** `user_id: uuid.UUID = Depends(require_current_user_id)`
- `AuthenticatedUser.current_user_id` is the same guard; use it only inside `app/user/` and `app/user/auth/`
- Import auth from the `app.user.auth` package, not from `app.user.auth.permissions` directly
- **Get email:** `email: str = Depends(AuthenticatedUser.current_user_email)`
- Session-based with Bearer token transport, argon2 hashing, DB-stored sessions

## Error Handling

- **Services/repositories:** raise domain exceptions (`NotFoundError`, `AuthenticationError`, etc.) with `from original_exc` to preserve context.
- **Routers:** do not catch exceptions — let them propagate to the FastAPI exception handlers and middleware, which log them. Exception: redirect-based OAuth endpoints may handle specific known exceptions at the router level.
- **External I/O (HTTP clients, OAuth):** catch protocol-level exceptions and wrap them in domain exceptions with `from err`.
- Do not use `raise ... from None`, because it drops the original exception context that debugging needs.
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

## Package `__init__.py` Convention
- Every package directory has an `__init__.py`, because missing init files cause inconsistent import behavior.
- Packages with a **public API** (re-exported symbols) define `__all__` (see `app/repositories/__init__.py`, `app/modules/items/__init__.py`).
- **Internal namespaces** with no re-exports keep `__init__.py` empty (a one-line docstring is fine).

## New Entities

Create in `app/modules/` following the items module pattern. Use `/skill:add-backend-entity` for step-by-step guidance.

**Quick checklist:** models.py → schemas.py → repository.py → service.py → filters.py → dependencies.py → routers.py → register in `app/routers.py` → generate migration
