---
name: project-standards
description: Mandatory standards for every code change in this project (FastAPI backend in backend/, React + TanStack frontend in frontend/). Load it BEFORE you write or change any code here - new or changed endpoints, entities, models, migrations, services, filters, pages, routes, components, hooks, forms, e2e tests, refactors, bug fixes, config or dependency changes. It sets the layering, file layout, naming, error contract, auth, logging, filters and pagination, frontend data fetching, the end-to-end-only test rules, and the Definition of Done.
---

# Project standards

Any agent can follow this file: open it, obey the rules, then open the
reference for your task. Paths are relative to the project root (the folder
with `docker-compose.yml`).

- The code is the source of truth. When this file and the code disagree, the
  code wins. Fix this file in the same change.
- Copy the reference features. Do not invent new patterns:
  - Backend: `backend/app/modules/items/`
  - Frontend: `frontend/src/routes/_authed/items.tsx`, `frontend/src/hooks/useItems.ts`
  - Tests: `backend/tests/e2e/test_items.py`, `frontend/e2e/items.spec.ts`

## References

| Task | Open |
|---|---|
| Add or change a backend resource (model, schema, repository, service, router, migration) | [references/backend-entity.md](references/backend-entity.md) |
| Add or change a list endpoint, filter, sort or page | [references/filters-pagination.md](references/filters-pagination.md) |
| Add logging, read the wide event, add a middleware | [references/logging.md](references/logging.md) |
| Add or change a page, hook, form, dialog or API call | [references/frontend-feature.md](references/frontend-feature.md) |
| Write or fix any test, or understand a guard failure | [references/e2e-testing.md](references/e2e-testing.md) |

## 1. Backend rules (`backend/`)

**Layering: Router -> Service -> Repository.** Never skip a layer.

| Layer | File | Does | Never |
|---|---|---|---|
| Router | `routers.py` | HTTP only: params, `Depends`, `log_action`, `Model.model_validate(...)` | business logic, SQL, `try/except` |
| Service | `service.py` | all business logic, ownership checks; subclass `BaseService[T]` (`app/services/base_crud_service.py`) | HTTP objects, raw sessions |
| Repository | `repository.py` | data access only; subclass `SQLAlchemyRepository[T]` (`app/repositories/sql_repository.py`), set `model = ...` | business rules |

- **Module layout:** `app/modules/<name>/` has `__init__.py` (with `__all__`),
  `models.py`, `schemas.py`, `repository.py`, `service.py`, `filters.py`,
  `dependencies.py`, `routers.py`.
- **Registration:** include the router in `app/routers.py`. Import the model
  module in `app/migrations/env.py` (explicit registry), or autogenerate does
  not see the table.
- **Migrations:** every model change needs an Alembic migration
  (`cd backend && uv run alembic upgrade head && uv run alembic revision
  --autogenerate -m "..."`; needs `backend/.env`; autogenerate fails if the
  database is not up to date). Run ruff on the new file, then review it.
  The backend test suite runs `alembic check` and fails on drift.
- **DI:** FastAPI `Depends()` with factory functions in `dependencies.py`
  (`get_<name>_service`, built on `get_repository(Repo)` from `app.dependencies`).
  No DI container.
- **Models:** SQLAlchemy 2 style (`Mapped[...]`, `mapped_column`), `uuid.uuid4`
  primary key, inherit `TimestampMixin, Base`. Enums: `enum.StrEnum`.
- **Schemas:** Pydantic 2. `<Name>Base` -> `<Name>Create`, `@partial_model`
  `<Name>Update` (from `app.core.optional_model`), `<Name>Response(<Name>Base, OrmBaseModel)`.
- **Auth guard:** feature routers use
  `dependencies=[Depends(require_current_user_id)]` and
  `user_id: uuid.UUID = Depends(require_current_user_id)`, imported from
  `app.user.auth`. Only `app/user/` uses `AuthenticatedUser.*`.
  User-owned data is scoped in the service; another user's row gives the same
  404 as a missing row.
- **Errors:** every error response is JSON `{detail, error_code}`.
  - Raise domain exceptions in services: `NotFoundError(detail=...)` from
    `app.repositories.exceptions`, or a new subclass of `HTTPExceptionMixin`
    (`app.exceptions`) with class attrs `status_code`, `detail`, `error_code`.
  - Routers do not catch exceptions. Wrap third-party errors with
    `raise DomainError(...) from err`. Never `from None`.
  - 422 = `error_code: "validation_error"`, `detail` = FastAPI's issue list.
    Unhandled errors = 500 `internal_server_error` (WideEventMiddleware).
- **Logging:** one wide event per request. In routers call `log_action("...")`
  (and `log_entity(...)` when the service does not). Free-form logs use
  `from loguru import logger`. No `print`. See [logging.md](references/logging.md).
- **List endpoints:** `pagination: Params = Depends()` and
  `x_filter: XFilter = FilterDepends(XFilter)`, return `Page[XResponse]`.
  Never plain `Depends()` for a filter.
- **Naming:** snake_case functions and variables, PascalCase classes,
  SCREAMING_SNAKE_CASE constants. Router object `<plural>_router`. URL prefix
  plural and kebab-case (`/items`).
- **Style:** ruff only (check + format, default line length 88). Type hints
  everywhere. Every package has `__init__.py`; public packages define `__all__`.
- **Run locally:** `cd backend && make run` (=`uv run uvicorn --factory app.main:create_app --reload --port 9095`).

## 2. Frontend rules (`frontend/`)

- **Pages:** file routes in `src/routes/`. Pages for signed-in users go in
  `src/routes/_authed/` (`_authed/items.tsx` is `/items`). Do not add auth
  redirects in `beforeLoad`: the token is in localStorage and the `_authed`
  layout (client-only, `ssr: false`) redirects after hydration.
  `src/routeTree.gen.ts` is generated by `bun run dev` / `bun run build`; never
  edit it by hand.
- **API calls:** only through `api` from `@/lib/api-client`. Every URL is in
  `API` in `src/lib/api-endpoints.ts`; query strings come from a builder there
  (e.g. `buildItemsListUrl`).
- **Server state:** TanStack Query hooks in `src/hooks/use<Feature>.ts`, keys
  from `src/lib/query-keys.ts`. Mutations invalidate `queryKeys.<feature>.all`.
  No `fetch` in components.
- **Types:** `src/types/<feature>.ts`, matching the backend response exactly.
- **Forms:** Zod schema in `src/features/<feature>/<entity>-schemas.ts`
  (e.g. `src/features/items/item-schemas.ts`) +
  react-hook-form + `zodResolver` + shadcn `Form` components. Server-rendered
  forms stay disabled until `useHydrated()` is true. Auth forms use `noValidate`.
- **Errors:** `toastApiError(error, 'What failed')` from `@/lib/error-handler`.
  `ApiError.code` = backend `error_code`; `ApiError.fields` only for 422.
- **Components:** flat in `src/components/` (`*Dialog.tsx` for dialogs);
  `src/components/ui/` is shadcn only. Style a Link as a button with
  `buttonVariants()` (Button has no `asChild`).
- **Imports:** `@/` = `src/`. Named exports, except the `Route` of route files.
- **Style:** ESLint + Prettier. `bun run lint`, `bun run format`, `bun run typecheck`.

## 3. Testing rules: end-to-end only

- **No unit tests. No mocks, fakes, patches, dependency overrides, network
  interception, in-process apps, fake clocks or SQLite.** Guards fail the run.
- **Every new or changed endpoint, page and feature gets e2e tests in the same
  change:**
  - Backend: `backend/tests/e2e/test_<feature>.py` against the live server
    (real Postgres, real migrations, real uvicorn, HTTP).
  - Frontend: `frontend/e2e/<feature>.spec.ts` (Playwright, real frontend +
    backend + Postgres), importing `{ test, expect } from './fixtures'`.
- Seed data through the public API. Use the `db` fixture only for state no
  endpoint can create (expiry, deactivation, emailed tokens).
- Third-party services: test every path that does not need the third party
  (validation, error redirects, "provider is down"). Never fake the provider.
- The route-coverage guards fail when any backend route has no successful
  request, any page is never visited, or any endpoint in `api-endpoints.ts` is
  never used by a spec or fixture.

## 4. Recipes in brief

**Add a backend entity** (full: [backend-entity.md](references/backend-entity.md)):
1. `models.py` -> 2. `schemas.py` -> 3. `repository.py` -> 4. `service.py`
-> 5. `filters.py` -> 6. `dependencies.py` -> 7. `routers.py` -> 8. `__init__.py`
-> 9. include router in `app/routers.py` -> 10. import model in
`app/migrations/env.py` -> 11. autogenerate the migration (needs `backend/.env`), ruff-fix and review it
-> 12. `tests/e2e/test_<name>.py` + a `create_<name>` helper in
`tests/e2e/helpers.py` -> 13. Definition of Done.

**Add a frontend feature** (full: [frontend-feature.md](references/frontend-feature.md)):
1. `types/<feature>.ts` -> 2. endpoints in `lib/api-endpoints.ts` -> 3. keys
in `lib/query-keys.ts` -> 4. Zod schema in `features/<feature>/` -> 5. hooks
in `hooks/use<Feature>.ts` -> 6. components/dialogs -> 7. route in
`routes/_authed/` -> 8. nav link in `components/Navigation.tsx` -> 9. seed
helpers in `e2e/fixtures.ts` + `e2e/<feature>.spec.ts` -> 10. Definition of Done.

## 5. Definition of Done

Run from the project root. All must pass before you call the work done.

| Check | Command |
|---|---|
| Static checks (backend ruff check + format --check; frontend lint, format:check, typecheck, build) | `make check` |
| Both e2e suites (backend API, then Playwright full stack), incl. route-coverage and no-mock guards | `make test` |
| Everything CI runs | `make ci` (= `make check` + `make test`) |

- Fix formatting with `make format` and lint with `make lint-fix`.
- Backend type check `make backend-typecheck` (ty) is advisory: do not add new
  diagnostics in code you touch, except the ones the `items` pattern already
  has (ty ignores the mypy-style `# type: ignore[override]` on the service
  overrides, and reports `invalid-type-form` on `<Entity>Update = Body(...)`).
- New behaviour has e2e tests. No test was skipped (`skip`, `only`, `fixme`).
- The migration exists and is reviewed when a model changed.
- Docs (`AGENTS.md`, this skill) still match the code you changed.
- New dependencies: pick a release at least 7 days old with no open
  critical/high CVE, pin it exactly (`"foo==1.2.3"` in `pyproject.toml`,
  `"foo": "1.2.3"` in `package.json`), and commit the lockfile (`uv.lock` /
  `bun.lock`) with it.
