---
name: fastapi-database-setup
description: Configure async SQLAlchemy 2.0 engine, session factory, and database dependency for FastAPI
---

# FastAPI Database Setup

## Overview

This skill covers setting up async SQLAlchemy 2.0 with PostgreSQL using asyncpg driver.

## Create database.py

Create `src/app/database.py`:

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# Create async engine
engine = create_async_engine(
    str(settings.database_url),
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,  # Verify connections before use
)

# Create async session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    
    Yields an async session and ensures it's closed after use.
    Uses the same session throughout the request lifecycle.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
```

## Create dependencies.py

Create `src/app/dependencies.py`:

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    
    Usage in routers:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
```

## Key Configuration Options

### Engine Options

| Option | Purpose | Default |
|--------|---------|---------|
| `echo` | Log all SQL statements | `False` |
| `pool_size` | Number of persistent connections | `5` |
| `max_overflow` | Additional connections allowed | `10` |
| `pool_pre_ping` | Test connection validity | `True` |
| `pool_recycle` | Recycle connections after N seconds | `-1` (disabled) |

### Session Options

| Option | Purpose | Recommended |
|--------|---------|-------------|
| `expire_on_commit` | Expire objects after commit | `False` |
| `autocommit` | Auto-commit transactions | `False` |
| `autoflush` | Auto-flush before queries | `False` |

## Why expire_on_commit=False?

In async contexts, accessing expired attributes triggers lazy loading, which fails outside an active session. Setting `expire_on_commit=False` allows accessing model attributes after commit without additional queries.

```python
# With expire_on_commit=True (default) - FAILS
async with session.begin():
    item = Item(name="test")
    session.add(item)
# item.name would fail here - object expired

# With expire_on_commit=False - WORKS
async with session.begin():
    item = Item(name="test")
    session.add(item)
# item.name works - object not expired
```

## Why autoflush=False?

Manual control over when changes are flushed to the database:
- Prevents unexpected queries during read operations
- Gives explicit control over transaction boundaries
- Avoids issues with lazy loading in async context

## Connection URL Format

PostgreSQL async connection string format:

```
postgresql+asyncpg://user:password@host:port/database
```

Examples:
```bash
# Local development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/myapp

# With SSL
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?ssl=require

# Connection pooler (e.g., PgBouncer)
DATABASE_URL=postgresql+asyncpg://user:pass@pgbouncer:6432/db?prepared_statement_cache_size=0
```

## Testing Configuration

For tests, use a separate test database:

```python
# In config.py, add:
test_database_url: PostgresDsn | None = None
```

```bash
# In .env.example, add:
TEST_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname_test
```

## Health Check Example

```python
from sqlalchemy import text

async def check_database_health(session: AsyncSession) -> bool:
    """Check if database is accessible."""
    try:
        await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
```

## Shutdown Cleanup

In your app factory, dispose the engine on shutdown:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()
```
