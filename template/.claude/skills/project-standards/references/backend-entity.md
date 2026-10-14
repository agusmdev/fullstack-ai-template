# Add a backend entity

Full recipe for a new resource in `backend/app/modules/<name>/`. Every snippet
is the real `items` module (`backend/app/modules/items/`) with the names
changed to a `notes` example. When in doubt, open the items file and copy it.

Run every command from `backend/`.

## File layout

```
app/modules/notes/
├── __init__.py       # re-exports, with __all__
├── models.py         # SQLAlchemy model
├── schemas.py        # Pydantic request/response models
├── repository.py     # data access (SQLAlchemyRepository)
├── service.py        # business logic (BaseService), ownership
├── filters.py        # fastapi-filter Filter for the list endpoint
├── dependencies.py   # get_note_service() factory
└── routers.py        # HTTP endpoints
```

Plus edits in `app/routers.py`, `app/migrations/env.py`, a new migration in
`app/migrations/versions/`, and tests in `tests/e2e/`.

## 1. Model (`models.py`)

```python
"""Note model."""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TimestampMixin


class Note(TimestampMixin, Base):
    __tablename__ = "note"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
```

- `TimestampMixin` (`app/database/mixins.py`) adds timezone-aware, indexed
  `created_at` / `updated_at`.
- `Base` (`app/database/base.py`) has a naming convention for constraints and
  indexes (`<table>_<col>_key`, `<col>_idx`, ...). Do not name them by hand
  unless you must match an existing migration (see `Item.__table_args__`).
- `__tablename__` is singular snake_case. It is also the `entity_type` in logs.
- Enum columns: `enum.StrEnum` (migrations use `alembic_postgresql_enum`).
- Drop `user_id` only if the data is not owned by a user.

## 2. Schemas (`schemas.py`)

```python
"""Note schemas - request and response models."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.optional_model import partial_model
from app.database.mixins import OrmBaseModel


class NoteBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)


class NoteCreate(NoteBase):
    pass


@partial_model
class NoteUpdate(NoteBase):
    """All fields omittable (PATCH)."""

    pass


class NoteResponse(NoteBase, OrmBaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
```

- `@partial_model`: every field can be omitted, but keeps its type. Explicit
  `null` is valid only for nullable fields (`description`); `{"name": null}`
  is a 422. The repository updates only the fields that were sent
  (`exclude_unset=True`).
- `OrmBaseModel` = `BaseModel` with `from_attributes=True`.
- Put limits (`min_length`, `max_length`) in the schema, so bad input is a 422
  `validation_error`, not a database error.
- Never put `user_id` in a Create/Update schema: the service sets it from the
  session.

## 3. Repository (`repository.py`)

```python
"""Note repository - database access layer."""

from app.modules.notes.models import Note
from app.repositories.sql_repository import SQLAlchemyRepository


class NoteRepository(SQLAlchemyRepository[Note]):
    model = Note
```

Inherited methods (`app/repositories/sql_repository.py`):

| Method | SQL |
|---|---|
| `get(entity_id, raise_error=True, response_model=None)` | SELECT by id; `NotFoundError` if missing and `raise_error` |
| `get_by_field(field, value, raise_error=True, response_model=None)` | SELECT by any column |
| `get_all(entity_filter=None, options=None)` | filtered SELECT -> `list[T]` |
| `get_all_paginated(pagination_params, entity_filter=None, options=None)` | filtered SELECT -> `Page[T]` |
| `create(entity, **extra_fields)` | INSERT ... RETURNING |
| `create_many(entities, on_conflict=conflict_passthrough)` | bulk INSERT ... RETURNING |
| `upsert(entity, **extra_fields)` | INSERT ... ON CONFLICT (id) DO UPDATE |
| `update(entity_id, entity)` | UPDATE ... RETURNING (only fields that were set) |
| `delete(entity_id)` / `delete_many(delete_filter_query)` | DELETE |

`QueryOptions` (`app/repositories/base_repository.py`) changes a query:
`base_query` (a `select(...)` to start from), `return_scalars`,
`response_model`, `pagination_kwargs`.

Integrity errors become HTTP errors automatically: unique violation ->
`DuplicateError` (400 `duplicate_item`), foreign-key violation ->
`ReferencedError` (400 `referenced_item`). Add custom methods only for queries
the base methods cannot express.

## 4. Service (`service.py`)

The items service scopes every call to the owner. Copy it for user-owned data:

```python
"""Note service - business logic layer."""

import uuid

from fastapi_filter.base.filter import BaseFilterModel
from fastapi_pagination import Page, Params
from pydantic import BaseModel
from sqlalchemy import select

from app.modules.notes.models import Note
from app.modules.notes.repository import NoteRepository
from app.repositories.base_repository import QueryOptions
from app.repositories.exceptions import NotFoundError
from app.services.base_crud_service import BaseService


class NoteService(BaseService[Note]):
    def __init__(self, repo: NoteRepository) -> None:
        self.repo = repo

    @staticmethod
    def _owned_or_404(note: Note | None, user_id: uuid.UUID, detail: str) -> Note:
        # Another user's note gets the exact error of a missing note.
        if note is None or note.user_id != user_id:
            raise NotFoundError(detail=detail)
        return note

    async def get_by_id(self, entity_id: uuid.UUID, *, user_id: uuid.UUID) -> Note:  # type: ignore[override]  # adds required user_id to enforce ownership
        note = await self.repo.get(entity_id, raise_error=False)
        return self._owned_or_404(note, user_id, f"Note {entity_id} not found")

    async def get_all_paginated(  # type: ignore[override]  # adds required user_id to scope the list
        self,
        pagination_params: Params,
        entity_filter: BaseFilterModel | None = None,
        *,
        user_id: uuid.UUID,
    ) -> Page[Note]:
        base_query = select(Note).where(Note.user_id == user_id)
        opts = QueryOptions(base_query=base_query)
        return await self.repo.get_all_paginated(pagination_params, entity_filter, opts)

    async def create(self, entity: BaseModel, *, user_id: uuid.UUID) -> Note:  # type: ignore[override]
        return await super().create(entity, user_id=user_id)

    async def update(
        self, entity_id: uuid.UUID, entity: BaseModel, *, user_id: uuid.UUID
    ) -> Note:  # type: ignore[override]
        await self.get_by_id(entity_id, user_id=user_id)
        return await super().update(entity_id, entity)

    async def delete(self, entity_id: uuid.UUID, *, user_id: uuid.UUID) -> None:  # type: ignore[override]
        await self.get_by_id(entity_id, user_id=user_id)
        await super().delete(entity_id)
```

- `BaseService` (`app/services/base_crud_service.py`) already logs the entity
  (`entity_type` = table name, `entity_id`) on single reads and all writes.
- Business errors: raise `NotFoundError(detail=...)` or your own exception
  (see "Errors" below). Never return `None` for "not found" to a router.

## 5. Filter (`filters.py`)

```python
"""Note filters."""

from app.core.filters import ModelFilter
from app.modules.notes.models import Note


class NoteFilter(ModelFilter):  # ?order_by= accepts model columns only (else 422)
    """?search=, ?name__ilike=%pattern%, ?order_by=-created_at"""

    order_by: list[str] = ["created_at"]
    name__ilike: str | None = None
    search: str | None = None

    class Constants(ModelFilter.Constants):
        model = Note
        search_model_fields = ["name", "description"]
```

Operators, sorting and pagination: [filters-pagination.md](filters-pagination.md).

## 6. Dependencies (`dependencies.py`)

```python
"""Dependency factory functions for Note module."""

from fastapi import Depends

from app.dependencies import get_repository
from app.modules.notes.repository import NoteRepository
from app.modules.notes.service import NoteService


def get_note_service(
    repo: NoteRepository = Depends(get_repository(NoteRepository)),
) -> NoteService:
    return NoteService(repo=repo)
```

`get_repository(Repo)` gives the repository a request-scoped `AsyncSession`
(`app/dependencies/__init__.py`). The session commits on success and rolls
back on error.

## 7. Router (`routers.py`)

```python
"""Notes router - CRUD endpoints."""

import uuid

from fastapi import APIRouter, Body, Depends, status
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, Params

from app.core.logging import log_action, log_entity
from app.modules.notes.dependencies import get_note_service
from app.modules.notes.filters import NoteFilter
from app.modules.notes.schemas import NoteCreate, NoteResponse, NoteUpdate
from app.modules.notes.service import NoteService
from app.user.auth import require_current_user_id

notes_router = APIRouter(
    prefix="/notes",
    tags=["notes"],
    dependencies=[Depends(require_current_user_id)],
)


@notes_router.get("", status_code=status.HTTP_200_OK)
async def list_notes(
    pagination: Params = Depends(),
    # FilterDepends, not Depends(): plain Depends() reads list fields
    # (order_by) from the request body.
    note_filter: NoteFilter = FilterDepends(NoteFilter),
    user_id: uuid.UUID = Depends(require_current_user_id),
    note_service: NoteService = Depends(get_note_service),
) -> Page[NoteResponse]:
    log_action("list")
    result = await note_service.get_all_paginated(
        pagination_params=pagination,
        entity_filter=note_filter,
        user_id=user_id,
    )
    return Page[NoteResponse](
        items=[NoteResponse.model_validate(n) for n in result.items],
        total=result.total,
        page=result.page,
        size=result.size,
        pages=result.pages,
    )


@notes_router.get("/{note_id}", status_code=status.HTTP_200_OK)
async def get_note(
    note_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    note_service: NoteService = Depends(get_note_service),
) -> NoteResponse:
    log_action("get")
    result = await note_service.get_by_id(note_id, user_id=user_id)
    return NoteResponse.model_validate(result)


@notes_router.post("", status_code=status.HTTP_201_CREATED)
async def create_note(
    note: NoteCreate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    note_service: NoteService = Depends(get_note_service),
) -> NoteResponse:
    log_action("create")
    result = await note_service.create(note, user_id=user_id)
    log_entity("note", result.id)
    return NoteResponse.model_validate(result)


@notes_router.patch("/{note_id}", status_code=status.HTTP_200_OK)
async def update_note(
    note_id: uuid.UUID,
    note: NoteUpdate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    note_service: NoteService = Depends(get_note_service),
) -> NoteResponse:
    log_action("update")
    log_entity("note", note_id)
    result = await note_service.update(note_id, note, user_id=user_id)
    return NoteResponse.model_validate(result)


@notes_router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    note_service: NoteService = Depends(get_note_service),
) -> None:
    log_action("delete")
    log_entity("note", note_id)
    await note_service.delete(note_id, user_id=user_id)
```

Rules:
- Auth: `require_current_user_id` from `app.user.auth` (the package, not
  `app.user.auth.permissions`). `AuthenticatedUser.*` is for `app/user/` only.
- Return `XResponse.model_validate(...)`. No `cast`, no raw ORM objects.
- `log_entity("<table name>", id)`: same lowercase name the service uses.
- No `try/except` in routers.

## 8. Package (`__init__.py`)

```python
"""Notes module."""

from .filters import NoteFilter
from .models import Note
from .repository import NoteRepository
from .routers import notes_router
from .schemas import NoteCreate, NoteResponse, NoteUpdate
from .service import NoteService

__all__ = [
    "Note",
    "NoteCreate",
    "NoteResponse",
    "NoteUpdate",
    "NoteFilter",
    "NoteRepository",
    "NoteService",
    "notes_router",
]
```

## 9. Register the router (`app/routers.py`)

```python
from app.modules.notes.routers import notes_router

def get_app_router() -> APIRouter:
    router = APIRouter()
    # ... auth_router, user_router, items_router ...
    router.include_router(notes_router)
    return router
```

## 10. Register the model (`app/migrations/env.py`)

```python
import app.modules.items.models  # noqa: F401, E402
import app.modules.notes.models  # noqa: F401, E402
```

`target_metadata = Base.metadata` sees only imported models. Without this
line, autogenerate does not create the table.

## 11. Migration

Alembic runs on your machine (not in the container), so it needs
`backend/.env`. The Docker-first setup does not create it:

```bash
docker compose up -d db          # from the project root, if no db is running
cd backend
cp .env.example .env             # once; DB_URL must match POSTGRES_* in the root .env
uv run alembic upgrade head      # first: autogenerate fails on a database that is not up to date
uv run alembic revision --autogenerate -m "add note table"
uv run ruff check --fix app/migrations && uv run ruff format app/migrations
uv run alembic upgrade head
```

- `make migrate-new msg="..."` in `backend/`, or `make migrate-create message="..."`
  at the root, run the same autogenerate.
- Without `backend/.env`, Alembic uses the `config.py` default. The generator
  sets that default to the generated `POSTGRES_*` values
  (`N:N@localhost:5432/N` for project `N`), so it works with an unchanged root
  `.env`. You need `backend/.env` only when you change `POSTGRES_*` or
  `DB_PORT` in the root `.env`; else Alembic fails with `password
  authentication failed` or cannot connect.
- The autogenerated file uses `typing.Union` / `Sequence`, which ruff rejects
  (UP035, UP007, I001). Run the ruff line above (or `make lint-all` in
  `backend/`), or `make check` fails.

Review the file in `app/migrations/versions/`: table name, every column and
type, `nullable`, indexes, unique constraints, foreign keys with `ondelete`,
enum types. The backend test suite runs `alembic check` on start: a model
change without a matching migration fails the whole suite.

## 12. Errors

Contract: every error is JSON `{detail, error_code}` (`app.exceptions.ErrorResponse`).

| Case | Status | `error_code` |
|---|---|---|
| `NotFoundError` | 404 | `not_found` |
| `DuplicateError` (unique) | 400 | `duplicate_item` |
| `ReferencedError` (foreign key) | 400 | `referenced_item` |
| Request validation (body, query, path) | 422 | `validation_error` (`detail` = FastAPI issue list) |
| Text with a NUL character | 422 | `validation_error` |
| Unknown path / wrong method | 404 / 405 | `http_error` |
| Plain `HTTPException` | its status | `http_error` |
| Unhandled exception | 500 | `internal_server_error` |
| No `Authorization` header | 403 | `http_error` (`"Not authenticated"`) |
| Unknown session / expired / inactive user | 401 | `invalid_session` / `session_expired` / `inactive_user` |

New domain error:

```python
from app.exceptions import HTTPExceptionMixin


class NoteLockedError(HTTPExceptionMixin):
    detail = "Note is locked"
    error_code = "note_locked"
    status_code = 409
```

Put it in the module (e.g. `app/modules/notes/exceptions.py`) and raise it in
the service. Third-party I/O: catch the client's protocol errors and
`raise MyDomainError() from err`. Never `from None`. The generic httpx wrapper
for third-party APIs is `ExternalApiService` in
`app/integrations/http_client.py` (no caller by default).

## 13. Tests (mandatory)

Write `tests/e2e/test_notes.py` and a `create_note` helper in
`tests/e2e/helpers.py`. Cover at least: create (201 + follow-up GET), list
(filters, order, pages), get, update, delete, validation (422), another user's
note (404), and no auth (403). The route-coverage guard fails until every new
route has a successful request. See [e2e-testing.md](e2e-testing.md).

If the frontend uses the endpoint, also follow [frontend-feature.md](frontend-feature.md).

## Checklist

- [ ] `models.py` (`TimestampMixin, Base`, UUID pk)
- [ ] `schemas.py` (Base / Create / `@partial_model` Update / Response)
- [ ] `repository.py` (`SQLAlchemyRepository[T]`, `model = ...`)
- [ ] `service.py` (`BaseService[T]`, ownership)
- [ ] `filters.py` (`order_by`, `search_model_fields`)
- [ ] `dependencies.py` (`get_<name>_service`)
- [ ] `routers.py` (`require_current_user_id`, `FilterDepends`, `log_action`)
- [ ] `__init__.py` with `__all__`
- [ ] router included in `app/routers.py`
- [ ] model imported in `app/migrations/env.py`
- [ ] migration generated (with `backend/.env` present), ruff-fixed, reviewed, applied
- [ ] `tests/e2e/test_<name>.py` + helper; `make check` and `make test` green
