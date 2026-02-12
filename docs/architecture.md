# Backend Architecture

This document describes the 3-layer FastAPI backend architecture, folder structure, and request flow.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Folder Structure](#folder-structure)
3. [Three-Layer Pattern](#three-layer-pattern)
4. [Request Flow](#request-flow)
5. [Core Components](#core-components)
6. [Authentication & Authorization](#authentication--authorization)
7. [Exception Handling](#exception-handling)
8. [Technology Stack](#technology-stack)

---

## Architecture Overview

The backend follows a **3-layer architecture** with clear separation of concerns:

```
HTTP Request
    ↓
APIRouter Layer (HTTP handling)
    ↓
Service Layer (Business logic)
    ↓
Repository Layer (Data access)
    ↓
Database (PostgreSQL)
```

### Core Principles

- **Separation of Concerns**: Each layer has a single responsibility
- **Dependency Injection**: FastAPI dependencies enable testability
- **Type Safety**: Full typing with Pydantic v2 and SQLAlchemy 2.0
- **Async Throughout**: Non-blocking I/O for scalability
- **Generic Base Classes**: Reduce boilerplate, enforce patterns

---

## Folder Structure

```
backend/
├── src/app/
│   ├── main.py                       # App factory, lifespan, middleware
│   ├── _cli.py                       # CLI commands
│   │
│   ├── core/                         # Core infrastructure
│   │   ├── config.py                 # Settings from environment
│   │   ├── database.py               # SQLAlchemy engine & sessions
│   │   ├── logging.py                # Structured logging
│   │   ├── models.py                 # Base model with mixins
│   │   ├── repositories/
│   │   │   ├── base.py               # Abstract BaseRepository
│   │   │   └── postgres.py           # PostgreSQL implementation
│   │   └── services/
│   │       └── base.py               # Abstract BaseService
│   │
│   ├── models/                       # Domain entities
│   │   ├── user.py                   # User model
│   │   ├── user_schemas.py           # UserCreate, UserUpdate, UserResponse
│   │   ├── user_repository.py        # UserRepository
│   │   ├── user_service.py           # UserService
│   │   ├── item.py                   # Item model
│   │   ├── item_schemas.py           # Item schemas + ItemFilter
│   │   ├── item_repository.py        # ItemRepository
│   │   ├── item_service.py           # ItemService
│   │   ├── session.py                # Session model (auth tokens)
│   │   ├── session_schemas.py        # Session schemas
│   │   ├── session_repository.py     # SessionRepository
│   │   └── session_service.py        # SessionService
│   │
│   ├── api/                          # HTTP endpoints
│   │   ├── __init__.py               # Main api_router
│   │   └── v1/
│   │       ├── __init__.py           # v1 router
│   │       ├── auth/                 # Authentication endpoints
│   │       │   ├── login.py
│   │       │   ├── logout.py
│   │       │   ├── me.py
│   │       │   └── register.py
│   │       ├── items/
│   │       │   └── router.py         # CRUD for items
│   │       └── ai/
│   │           └── extract.py        # AI extraction demo
│   │
│   ├── ai/                           # AI provider abstraction
│   │   ├── factory.py                # Provider factory
│   │   └── providers/
│   │       ├── base.py               # Abstract AIProvider
│   │       ├── mock_provider.py      # Mock (default)
│   │       ├── openai_provider.py    # OpenAI integration
│   │       ├── anthropic_provider.py # Anthropic Claude
│   │       └── azure_provider.py     # Azure OpenAI
│   │
│   ├── common/                       # Cross-cutting concerns
│   │   ├── dependencies.py           # Dependency injection
│   │   ├── exceptions.py             # Custom exceptions
│   │   ├── exception_handlers.py     # Global handlers
│   │   └── schemas.py                # Base schemas
│   │
│   ├── middleware/
│   │   └── correlation_id.py         # Request correlation IDs
│   │
│   └── jobs/                         # Background jobs
│       └── cleanup_sessions.py       # APScheduler session cleanup
│
├── alembic/                          # Database migrations
├── tests/                            # Test suite
├── pyproject.toml                    # Dependencies & config
├── alembic.ini                       # Alembic configuration
└── .env.example                      # Environment template
```

---

## Three-Layer Pattern

### Layer 1: API/Router Layer

**Location**: `api/v1/{domain}/router.py`

**Responsibility**: HTTP request handling, input validation, response serialization

**Example - Items Router**:
```python
# api/v1/items/router.py
@router.get("/items", response_model=Page[ItemResponse])
async def list_items(
    current_user: User = Depends(get_current_user),
    item_service: ItemService = Depends(get_item_service),
    params: Params = Depends(),
    item_filter: ItemFilter = FilterDepends(ItemFilter),
) -> Page[ItemResponse]:
    return await item_service.get_user_items_paginated(
        current_user.id, params, item_filter
    )
```

**Key Characteristics**:
- Uses FastAPI dependencies for injection
- Authentication via `get_current_user` dependency
- Returns Pydantic schemas (e.g., `ItemResponse`)
- Handles status codes and errors via exceptions
- No business logic - delegates to service layer

### Layer 2: Service Layer

**Location**: `models/{entity}_service.py`, inherits from `core/services/base.py`

**Responsibility**: Business logic, validation, authorization, orchestration

**Example - ItemService**:
```python
# models/item_service.py
class ItemService(BaseService[Item, ItemCreate, ItemUpdate, ItemFilter]):
    async def create_item(self, item_data: ItemCreate, user_id: UUID) -> Item:
        # Business logic: create with user ownership
        item = Item(
            title=item_data.title,
            description=item_data.description,
            user_id=user_id,
        )
        self.repository.session.add(item)
        await self.repository.session.flush()
        return item

    async def delete_item(self, item_id: UUID, user_id: UUID) -> None:
        # Authorization: check ownership
        item = await self.repository.get(item_id)
        if item.user_id != user_id:
            raise ForbiddenError("Not authorized")
        await self.repository.soft_delete(item_id)
```

**Key Characteristics**:
- Lifecycle hooks: `before_create`, `after_create`, `before_update`, `after_update`
- Delegates database operations to repository
- Implements authorization checks
- Raises domain-specific exceptions
- No direct SQL/ORM queries

### Layer 3: Repository Layer

**Location**: `models/{entity}_repository.py`, inherits from `core/repositories/postgres.py`

**Responsibility**: Database access, query building, ORM operations

**Example - ItemRepository**:
```python
# models/item_repository.py
class ItemRepository(PostgresRepository[Item, ItemCreate, ItemUpdate, ItemFilter]):
    async def get_by_user(self, user_id: UUID) -> list[Item]:
        query = self._base_query().where(Item.user_id == user_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_paginated_by_user(
        self, user_id: UUID, params: Params, item_filter: ItemFilter | None = None
    ) -> AbstractPage[Item]:
        query = self._base_query().where(Item.user_id == user_id)
        if item_filter is not None:
            query = item_filter.filter(query)
            query = item_filter.sort(query)
        return await paginate(self.session, query, params)
```

**Key Characteristics**:
- Extends `PostgresRepository` (provides CRUD operations)
- Handles all database queries
- Automatic soft-delete filtering via `_base_query()`
- Pagination support via `fastapi-pagination`
- Custom filters via `fastapi-filter`
- No business logic

---

## Request Flow

### Example: POST /api/v1/items (Create Item)

```
1. HTTP POST /api/v1/items
   Body: {"title": "My Item", "description": "..."}
   Headers: Authorization: Bearer <token>

   ↓

2. [FastAPI] Request validation
   - Validates JSON body against ItemCreate schema
   - Extracts dependencies

   ↓

3. [Dependency: get_current_user]
   - Calls get_current_session(authorization header)
   - SessionService.get_active_session(token)
   - SessionRepository.get_by_token(token)
   - Validates session not expired
   - UserRepository.get_by_id(session.user_id)
   - Returns User object

   ↓

4. [Dependency: get_item_service]
   - Creates ItemService with ItemRepository

   ↓

5. [Router] api/v1/items/router.py
   - Calls item_service.create_item(item_data, current_user.id)

   ↓

6. [Service] ItemService.create_item
   - Applies business logic (set user_id)
   - Creates Item instance
   - Adds to session via repository
   - Flushes to generate id

   ↓

7. [Repository] PostgresRepository (implicit)
   - session.add(item)
   - session.flush()
   - session.refresh(item)

   ↓

8. [Database] PostgreSQL
   - INSERT INTO items (id, title, description, user_id, created_at, updated_at)
   - Returns generated values

   ↓

9. [Response] ItemResponse serialization
   - Converts ORM Item to Pydantic ItemResponse
   - HTTP 201 Created
   - JSON: {"id": "...", "title": "...", "created_at": "...", ...}
```

### Error Flow

If any exception occurs:

```
Exception raised (e.g., NotFoundError, ForbiddenError)
    ↓
Global Exception Handler (common/exception_handlers.py)
    ↓
ErrorResponse schema
    ↓
HTTP error response (404, 403, etc.)
JSON: {"detail": "...", "status_code": 404}
```

---

## Core Components

### Base Model & Mixins

**File**: `core/models.py`

```python
class UUIDMixin:
    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

class TimestampMixin:
    created_at: datetime = Column(DateTime, default=func.now())
    updated_at: datetime = Column(DateTime, default=func.now(), onupdate=func.now())

class SoftDeleteMixin:
    deleted_at: datetime | None = Column(DateTime, nullable=True)

class BaseModel(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __abstract__ = True
```

**All models inherit from `BaseModel`** → automatic UUID primary key, timestamps, soft-delete support.

### Generic Repository Pattern

**Interface**: `core/repositories/base.py` (abstract)
**Implementation**: `core/repositories/postgres.py` (concrete)

```python
class BaseRepository(ABC, Generic[ModelT, CreateSchemaT, UpdateSchemaT, FilterT]):
    """Abstract repository interface"""

    # CRUD operations
    async def create(self, obj_in: CreateSchemaT) -> ModelT
    async def get(self, id: Any) -> ModelT | None
    async def get_all(self) -> list[ModelT]
    async def update(self, id: Any, obj_in: UpdateSchemaT) -> ModelT
    async def delete(self, id: Any) -> bool
    async def soft_delete(self, id: Any) -> bool

    # Advanced operations
    async def bulk_create(self, objs_in: list[CreateSchemaT]) -> list[ModelT]
    async def get_or_create(self, obj_in: CreateSchemaT, **filters) -> tuple[ModelT, bool]
    async def count(self) -> int
    async def exists(self, id: Any) -> bool
```

**Entity repositories inherit and customize**:
```python
class ItemRepository(PostgresRepository[Item, ItemCreate, ItemUpdate, ItemFilter]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Item)

    # Add entity-specific queries
    async def get_by_user(self, user_id: UUID) -> list[Item]: ...
```

### Generic Service Pattern

**Base**: `core/services/base.py`

```python
class BaseService(Generic[ModelT, CreateSchemaT, UpdateSchemaT, FilterT]):
    """Service layer with lifecycle hooks"""

    def __init__(self, repository: BaseRepository):
        self.repository = repository

    # Lifecycle hooks (override in subclasses)
    async def before_create(self, data: CreateSchemaT) -> CreateSchemaT: ...
    async def after_create(self, entity: ModelT) -> None: ...

    # CRUD operations with hooks
    async def create(self, data: CreateSchemaT) -> ModelT:
        data = await self.before_create(data)
        entity = await self.repository.create(data)
        await self.after_create(entity)
        return entity
```

**Example hook usage**:
```python
class UserService(BaseService[User, UserCreate, UserUpdate, None]):
    async def before_create(self, data: UserCreate) -> User:
        # Check email conflict
        if await self.repository.email_exists(data.email):
            raise ConflictError(f"Email {data.email} already exists")

        # Hash password
        user = User(email=data.email, password_hash="")
        user.set_password(data.password)
        return user
```

### Database Session Management

**File**: `core/database.py`

```python
# Engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before use
    echo=settings.environment == "development",
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency for route handlers
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**Usage in endpoints**:
```python
@router.get("/items")
async def list_items(
    session: AsyncSession = Depends(get_session),
    ...
):
    # session is auto-committed or rolled back
```

---

## Authentication & Authorization

### Registration Flow

```
POST /api/v1/auth/register
Body: {"email": "user@example.com", "password": "..."}
    ↓
[Router] register.py
    ↓
[Service] UserService.create_user
    - Validates email uniqueness
    - Hashes password with argon2
    - Creates User in database
    ↓
[Service] SessionService.create_session
    - Generates secure token (secrets.token_urlsafe)
    - Stores session with expiration (24h default)
    - Records IP address and user agent
    ↓
[Response] 201 Created
JSON: {
    "user": {"id": "...", "email": "..."},
    "token": "abc123...",
    "session": {"id": "...", "expires_at": "..."}
}
```

### Authentication Flow (Protected Routes)

**Dependency chain**: `get_session` → `get_current_session` → `get_current_user`

```python
# common/dependencies.py

async def get_current_session(
    authorization: str = Header(...),
    session_service: SessionService = Depends(get_session_service),
) -> Session:
    """Extract and validate Bearer token"""

    # Parse "Bearer <token>"
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Invalid authorization header")

    token = authorization.split(" ")[1]

    # Validate session exists and not expired
    session = await session_service.get_active_session(token)
    if not session:
        raise UnauthorizedError("Invalid or expired token")

    return session

async def get_current_user(
    session: Session = Depends(get_current_session),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """Load user from validated session"""

    user = await user_service.get_user_by_id(session.user_id)
    if not user:
        raise UnauthorizedError("User not found")

    return user
```

**Usage in endpoints**:
```python
@router.get("/items")
async def list_items(
    current_user: User = Depends(get_current_user),  # Auto validates token
    ...
):
    # current_user is guaranteed valid
```

### Authorization Pattern

**Ownership checks in service layer**:

```python
# models/item_service.py
async def delete_item(self, item_id: UUID, user_id: UUID) -> None:
    item = await self.repository.get(item_id)

    if not item:
        raise NotFoundError(f"Item {item_id} not found")

    if item.user_id != user_id:
        raise ForbiddenError("Not authorized to delete this item")

    await self.repository.soft_delete(item_id)
```

---

## Exception Handling

### Exception Hierarchy

**File**: `common/exceptions.py`

```python
class AppError(Exception):
    """Base exception for all app errors"""
    def __init__(self, detail: str, status_code: int = 500):
        self.detail = detail
        self.status_code = status_code

class NotFoundError(AppError):
    """404 - Resource not found"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail, status_code=404)

class ConflictError(AppError):
    """409 - Resource conflict (e.g., duplicate email)"""
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(detail, status_code=409)

class BadRequestError(AppError):
    """400 - Invalid request"""
    def __init__(self, detail: str = "Bad request"):
        super().__init__(detail, status_code=400)

class UnauthorizedError(AppError):
    """401 - Authentication required"""
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(detail, status_code=401)

class ForbiddenError(AppError):
    """403 - Insufficient permissions"""
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(detail, status_code=403)
```

### Global Exception Handlers

**File**: `common/exception_handlers.py`

```python
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle all AppError subclasses"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            status_code=exc.status_code,
        ).model_dump(),
    )

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors (422)"""
    errors = []
    for error in exc.errors():
        errors.append(ErrorDetail(
            field=".".join(str(loc) for loc in error["loc"]),
            message=error["msg"],
            type=error["type"],
        ))

    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            detail="Validation error",
            status_code=422,
            errors=errors,
        ).model_dump(),
    )
```

**Usage in code**:
```python
# Anywhere in the codebase
if not item:
    raise NotFoundError(f"Item {item_id} not found")

# Results in:
# HTTP 404
# {"detail": "Item abc-123 not found", "status_code": 404}
```

---

## Technology Stack

### Core Framework
- **FastAPI 0.128+**: Modern async web framework
- **Uvicorn**: ASGI server
- **Pydantic v2**: Data validation & serialization

### Database
- **SQLAlchemy 2.0+**: Async ORM
- **asyncpg**: Async PostgreSQL driver
- **Alembic**: Database migrations

### Features
- **fastapi-pagination**: Automatic pagination
- **fastapi-filter**: Advanced filtering & sorting
- **argon2-cffi**: Secure password hashing
- **APScheduler**: Background job scheduling
- **instructor**: Structured AI output parsing

### AI Providers
- **OpenAI API**: GPT models
- **Anthropic Claude**: Claude models
- **Azure OpenAI**: Azure-hosted OpenAI
- **Mock provider**: Testing without API calls

### Development
- **pytest + pytest-asyncio**: Testing framework
- **Ruff**: Fast Python linter
- **uv**: Fast dependency management

---

## Key Design Decisions

### Why 3 Layers?

- **Testability**: Each layer can be tested independently
- **Flexibility**: Swap implementations (e.g., PostgreSQL → MongoDB)
- **Clarity**: Clear responsibility boundaries
- **Reusability**: Generic base classes reduce duplication

### Why Generic Base Classes?

- **DRY Principle**: CRUD logic written once
- **Type Safety**: Full typing with generics
- **Consistency**: All entities follow same patterns
- **Extensibility**: Override hooks for custom behavior

### Why Soft Deletes?

- **Data Recovery**: Accidental deletes can be recovered
- **Audit Trail**: Historical data preserved
- **Referential Integrity**: Foreign keys remain valid
- **Transparent**: `_base_query()` auto-filters deleted records

### Why Dependency Injection?

- **Testing**: Easy to mock dependencies
- **Decoupling**: Components don't create their dependencies
- **Flexibility**: Swap implementations without code changes
- **Clarity**: Explicit dependencies in function signatures

---

## Next Steps

For more information:
- **Conventions**: See [conventions.md](./conventions.md)
- **Troubleshooting**: See [troubleshooting.md](./troubleshooting.md)
- **Migrations**: See [MIGRATIONS.md](../template/backend/MIGRATIONS.md)
- **Testing**: See [tests/](../template/backend/tests/)
