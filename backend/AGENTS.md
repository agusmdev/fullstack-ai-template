# AGENTS.md — backend

**Before writing or changing code, read `.claude/skills/project-standards/SKILL.md` (at the project root, one level up: `../.claude/skills/project-standards/SKILL.md`) and follow it.** Start-up steps and the Definition of Done are in [../AGENTS.md](../AGENTS.md).

## Commands (run in `backend/`)

| Task | Command |
|---|---|
| Install deps | `uv sync` |
| Run the API (port 9095, reload) | `make run` = `uv run uvicorn --factory app.main:create_app --reload --port 9095` |
| All tests (e2e, needs Docker) | `make test` = `uv run pytest` |
| One test file / test | `uv run pytest tests/e2e/test_items.py` / `uv run pytest tests/e2e/test_items.py::test_name` |
| Tests + coverage | `make test-cov` (report in `htmlcov/`) |
| Lint + format (changes files) | `make lint-all` (`ruff check . --fix`, `ruff format .`) |
| Check only (what CI runs) | `make check` (`ruff check .`, `ruff format --check .`) |
| Type check (advisory) | `make backend-typecheck` at the root (runs `cd backend && uvx ty@0.0.84 check app`; version pinned by `TY_VERSION` in the root `Makefile`). Do not run `uvx ty` without a version: it fetches the newest release and skips the 7-day supply-chain floor. `ty` is not a dependency and reports known diagnostics; it is not in CI |
| New migration | `make migrate-new msg="add orders"` = `uv run alembic revision --autogenerate -m "..."` |
| Apply / undo migration | `make migrate` / `make migrate-down` |
| Git hooks | `make pre-commit` (install), `make pre-commit-all` (run on all files). Both use `../.pre-commit-config.yaml` |

`.env.example` is for runs **outside** Docker only (`cp .env.example .env`). Docker Compose does not read it: the container gets its settings from `../docker-compose.yml` and the root `.env`.

## Stack

Python 3.12, FastAPI 0.118 (async), SQLAlchemy 2 (`Mapped[]`, `mapped_column`, asyncpg), Pydantic 2, Alembic, fastapi-filter, fastapi-pagination, Loguru, argon2, uv. Ruff (`ruff==0.13.3`) is the linter and the formatter; default line length 88, E501 ignored. There is no black.

## Layout

```
app/
├── main.py           # create_app(): exception handlers, middleware (CORS → WideEvent), Sentry, /health
├── routers.py        # Registers every feature router
├── exceptions.py     # ErrorResponse {detail, error_code}, HTTPExceptionMixin
├── core/             # config.py (Settings), logging/, optional_model.py (partial_model)
├── database/         # Base, engine/session, mixins (TimestampMixin), db/ (select_from_pydantic)
├── repositories/     # BaseRepository, SQLAlchemyRepository, QueryOptions, on-conflict clauses, exceptions
├── services/         # BaseService (generic CRUD)
├── dependencies/     # get_engine (singleton), get_db_session, get_repository()
├── integrations/     # ExternalApiService: async httpx wrapper for third-party APIs (unused by default)
├── user/             # User model, /users/me routes
│   └── auth/         # Sessions, register/login/logout, password reset, email verification, Google OAuth
├── modules/          # Feature modules; items/ is the reference example
└── migrations/       # Alembic env.py + versions/
tests/
├── conftest.py       # Guard hooks (no mocks, route coverage)
└── e2e/              # The only test folder: conftest.py (fixtures), helpers.py, test_<feature>.py
```

New cross-cutting HTTP middleware goes in `app/middlewares/` (create it when needed). Middleware tied to one feature stays in its package (for example `app/core/logging/middleware.py`).

## Architecture

**Router → Service → Repository**, strict.

- **Router:** HTTP only. No business logic. Gets the service with `Depends(get_<x>_service)`.
- **Service:** all business logic. Inherits `BaseService[T]` (`app/services/base_crud_service.py`).
- **Repository:** data access only. Inherits `SQLAlchemyRepository[T]` (`app/repositories/sql_repository.py`).
- **Feature module:** `app/modules/<name>/` with `models.py`, `schemas.py`, `repository.py`, `service.py`, `filters.py`, `dependencies.py`, `routers.py`, `__init__.py`. Copy `app/modules/items/`.
- **DI:** FastAPI `Depends()` with factory functions (`get_repository(RepoType)` in `app/dependencies/`). No DI container.
- **PATCH schemas:** `@partial_model` (`app/core/optional_model.py`). Fields can be left out but keep their type; `null` is accepted only for nullable fields (else 422).
- **`__init__.py`:** every package has one. Packages with a public API set `__all__`.

## New entity checklist

1. `app/modules/<name>/` with the files above (copy `items/`).
2. Register the router in `app/routers.py`.
3. Import the model module in `app/migrations/env.py` (explicit list). If you skip this, autogenerate does not see the table.
4. `make migrate` first (autogenerate fails if the database is not up to date), then `make migrate-new msg="add <name>"` (needs `backend/.env`: `cp .env.example .env` once), then `make lint-all` (alembic output is not ruff-formatted), review the file, `make migrate`.
5. List endpoints: `item_filter: ItemFilter = FilterDepends(ItemFilter)` (from `fastapi_filter`) — not `Depends()`, which moves list fields such as `order_by` into the request body. Pagination: `Params = Depends()` (`page` default 1, `size` default 50, max 100).
6. Write `tests/e2e/test_<name>.py` (see Testing). Put a `create_<name>()` helper in `tests/e2e/helpers.py`.

## Filters

`ItemFilter` (`app/modules/items/filters.py`) declares `order_by` (default `["created_at"]`, `-field` = descending), `name__ilike` and `search` (name and description, case-insensitive).

For a new filter, declare `<field>__<op>` with op in `neq, gt, gte, lt, lte, in, not_in, isnull, not, like, ilike`. There is **no `__eq`**: equality uses the bare field name. Send `%` yourself for `like`/`ilike`.

## Auth

- Feature routes: `Depends(require_current_user_id)` from `app.user.auth` (see `app/modules/items/routers.py`). Import from the package, not from `app.user.auth.permissions`.
- Inside `app/user/`: `AuthenticatedUser.current_user_id` / `.get_current_user`.
- Sessions are DB rows; the client sends `Authorization: Bearer <session id>`. Passwords: argon2, at least 8 characters. Emails are stored lowercase. `User.is_active=False` blocks login and every request.
- OAuth callback redirects to `{FRONTEND_URL}/oauth/callback?session=<id>`, or `{FRONTEND_URL}/oauth/error?error=<code>` (`access_denied`, `missing_code`, `unsupported_provider`, `inactive_user`, ...).

## Error contract

Every error body is `{"detail": ..., "error_code": "..."}` (`app/exceptions.py` → `ErrorResponse`). There is no `fields` or `code` key.

| Case | Status | `error_code` |
|---|---|---|
| Request validation (incl. NUL in text) | 422 | `validation_error` (`detail` = FastAPI's list of `{loc, msg, type}` issues, or a string) |
| No `Authorization` header / non-Bearer scheme | 403 | `http_error` (`Not authenticated` / `Invalid authentication credentials`) |
| Unknown or revoked session | 401 | `invalid_session` |
| Expired session | 401 | `session_expired` |
| Inactive user | 401 | `inactive_user` |
| Login: unknown or inactive user / wrong password | 401 | `authentication_error` / `invalid_password` |
| Not found (missing, or owned by another user) | 404 | `not_found` |
| Unique / foreign-key violation | 400 | `duplicate_item` / `referenced_item` |
| Router 404/405, plain `HTTPException` | — | `http_error` |
| Unhandled exception | 500 | `internal_server_error` |

- Services and repositories raise domain exceptions (subclass `HTTPExceptionMixin` with `status_code`, `detail`, `error_code`). Keep the cause: `raise X(...) from err`. Never `from None`.
- Routers do not catch exceptions (exception: the redirect-based OAuth callback).
- External I/O: catch protocol errors and wrap them in a domain exception with `from err` (example: `ExternalApiService` in `app/integrations/http_client.py`).

## Logging

`WideEventMiddleware` (`app/core/logging/middleware.py`) creates the `request_id` and writes one structured "wide event" per request. In code, add context with `log_action()`, `log_entity()`, `log_entities()`, `log_custom()` from `app.core.logging`; the auth dependency calls `log_user()`. For plain log lines use `from loguru import logger`. Values of sensitive keys (names that contain `password`, `token`, `secret`, `api_key`, `authorization`, `cookie`, ...) and the `code` and `session` query params are replaced with `[REDACTED]` (lists: `SENSITIVE_KEYS` and `SENSITIVE_QUERY_PARAMS` in `app/core/logging/sanitizer.py`).

## Testing (end-to-end only)

No unit tests, no mocks, no patches, no `dependency_overrides`, no TestClient/ASGI transport, no sqlite. The suite starts Postgres (testcontainers), runs `alembic upgrade head` and `alembic check`, starts the real `uvicorn` and sends HTTP.

- Put tests in `tests/e2e/test_<feature>.py`. Read the docstring of `tests/e2e/conftest.py` first; `tests/e2e/test_items.py` is the reference.
- Fixtures: `api`, `auth_client`, `register_user`, `make_client`, `server_log`, `db` (raw SQL only for state the API cannot create).
- Guards fail the run for a mock, a test outside `tests/e2e/`, an app import in tests, a route with no successful (<400) request, or a model change with no migration.

Full guide: `../.claude/skills/project-standards/references/e2e-testing.md`.
