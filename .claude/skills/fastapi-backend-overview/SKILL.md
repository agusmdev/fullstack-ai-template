---
name: fastapi-backend-overview
description: Overview and guidelines for FastAPI 3-layer architecture with async SQLAlchemy, Pydantic v2, and best practices
---

# FastAPI Backend Stack - Overview & Guidelines

## Architecture Overview

This stack follows a **3-layer architecture** with strict separation of concerns:

```
Router (API Layer) → Service (Business Logic) → Repository (Data Access) → Database
```

### Layer Responsibilities

| Layer | Responsibility | SQL Allowed | Imports |
|-------|---------------|-------------|---------|
| **Router** | HTTP handling, request validation, dependency injection | NO | Service, Schemas, Filters |
| **Service** | Business logic, orchestration, validation rules | NO | Repository, Schemas |
| **Repository** | Data access, SQL queries, database operations | YES | Models, SQLAlchemy |

## Project Structure (Entity-Based)

```
project/
├── pyproject.toml
├── .env.example
├── .python-version              # 3.12
├── ruff.toml
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py              # App factory
│       ├── config.py            # pydantic-settings
│       ├── database.py          # Async SQLAlchemy
│       ├── dependencies.py      # Shared dependencies (get_db)
│       ├── exceptions.py        # Custom exceptions
│       ├── exception_handlers.py
│       ├── logging.py           # Structured logging
│       ├── middleware/
│       │   ├── __init__.py
│       │   └── correlation_id.py
│       ├── core/                # Abstract base classes
│       │   ├── __init__.py
│       │   ├── models.py        # Base model, mixins
│       │   ├── schemas.py       # Base schemas
│       │   ├── repository.py    # AbstractRepository
│       │   └── service.py       # BaseService
│       ├── common/
│       │   ├── __init__.py
│       │   └── postgres_repository.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── v1/
│       │       ├── __init__.py
│       │       └── router.py
│       └── {entity}/            # Per-entity folders
│           ├── __init__.py
│           ├── models.py
│           ├── schemas.py
│           ├── repository.py
│           ├── service.py
│           ├── router.py
│           ├── dependencies.py
│           └── filters.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── api/v1/
```

## Core Technologies

- **Python**: 3.12+
- **Package Manager**: uv (required)
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0+ (async)
- **Database**: PostgreSQL with asyncpg
- **Validation**: Pydantic v2
- **Configuration**: pydantic-settings
- **Migrations**: Alembic (async)
- **Pagination**: fastapi-pagination
- **Filtering**: fastapi-filter
- **Linting**: ruff

## Key Design Decisions

### 1. UUID Primary Keys
All models use UUID primary keys for distributed system compatibility.

### 2. UTC Timestamps
All timestamps are timezone-aware UTC using `DateTime(timezone=True)`.

### 3. Soft Delete
Models support soft delete via `deleted_at` timestamp. Queries automatically filter deleted records.

### 4. Entity-Based Organization
Each entity (e.g., items, users) has its own folder containing all related files.

### 5. Generic Repository Pattern
Type-safe repositories using Python generics: `Repository[ModelType, CreateSchema, UpdateSchema]`

### 6. PostgreSQL-Specific Features
Bulk operations use PostgreSQL's `ON CONFLICT` for upserts.

## Data Flow

```
Request
  ↓
Middleware (Correlation ID)
  ↓
Router
  ├── Validates request (Pydantic)
  ├── Extracts filter params (fastapi-filter)
  └── Calls Service
        ↓
      Service
        ├── Applies business logic
        └── Calls Repository
              ↓
            Repository
              ├── Executes SQL (SQLAlchemy)
              └── Returns model instances
              ↑
            Database
```

## Error Handling

All errors return a consistent JSON structure:
```json
{
  "detail": "Resource not found",
  "error_code": "NOT_FOUND",
  "correlation_id": "uuid",
  "timestamp": "2025-01-05T12:00:00Z"
}
```

## Available Skills

Load specific skills for detailed implementation:

| Skill | Purpose |
|-------|---------|
| `fastapi-project-setup` | Initialize project with uv, dependencies, ruff |
| `fastapi-database-setup` | Async SQLAlchemy engine and session |
| `fastapi-core-models` | Base model and mixins |
| `fastapi-core-schemas` | Base Pydantic schemas |
| `fastapi-core-repository` | Abstract repository interface |
| `fastapi-postgres-repository` | PostgreSQL repository implementation |
| `fastapi-core-service` | Base service class |
| `fastapi-exceptions` | Custom exceptions and handlers |
| `fastapi-logging` | Structured logging with correlation IDs |
| `fastapi-app-factory` | FastAPI app factory and main.py |
| `fastapi-alembic-setup` | Async Alembic configuration |
| `fastapi-entity` | Create a new entity with all files |
| `fastapi-testing` | Test configuration and fixtures |

## Best Practices

1. **SQL Only in Repositories**: Never write SQLAlchemy queries outside repository layer
2. **Type Everything**: Use type hints everywhere, enable strict mypy
3. **Async All The Way**: Use async/await consistently
4. **Dependency Injection**: Use FastAPI's `Depends()` for all dependencies
5. **Validate Early**: Use Pydantic schemas at API boundary
6. **Log with Context**: Always include correlation_id in logs
7. **Handle Errors Gracefully**: Use custom exceptions, never raise generic ones
