---
name: fastapi-testing
description: Configure pytest-asyncio with test database fixtures and integration tests for FastAPI routers
---

# FastAPI Testing Setup

## Overview

This skill covers setting up pytest-asyncio for integration testing FastAPI routers with a test database.

## Test Configuration in pyproject.toml

Ensure `pyproject.toml` has:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
pythonpath = ["src"]
```

## Add Test Database URL to Config

Update `src/app/config.py`:

```python
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ... existing settings ...

    # Test database (optional, falls back to modifying database_url)
    test_database_url: PostgresDsn | None = None


settings = Settings()
```

Update `.env.example`:

```bash
# Test database
TEST_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname_test
```

## Create tests/conftest.py

Create `tests/conftest.py`:

```python
import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.core.models import Base
from app.dependencies import get_db
from app.main import app


# Get test database URL
def get_test_database_url() -> str:
    """Get the test database URL."""
    if settings.test_database_url:
        return str(settings.test_database_url)
    # Fallback: modify main database URL to use test database
    main_url = str(settings.database_url)
    return main_url.replace("/dbname", "/dbname_test")


# Create test engine
test_engine = create_async_engine(
    get_test_database_url(),
    echo=False,
    pool_pre_ping=True,
)

# Create test session factory
test_async_session_factory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an event loop for the test session.
    
    This fixture is required for session-scoped async fixtures.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """
    Set up the test database schema.
    
    Creates all tables before tests run and drops them after.
    Runs once per test session.
    """
    # Import all models to ensure they're registered
    from app.items.models import Item  # noqa: F401
    # Add other model imports here
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await test_engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session for a single test.
    
    Each test gets its own session with automatic rollback.
    This ensures test isolation.
    """
    async with test_async_session_factory() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP client for testing API endpoints.
    
    Overrides the database dependency to use the test session.
    """
    # Override the database dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Create async client
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def sample_item_data() -> dict:
    """Provide sample data for creating an item."""
    return {
        "name": "Test Item",
        "description": "A test item description",
    }


@pytest.fixture
async def created_item(
    client: AsyncClient,
    sample_item_data: dict,
) -> dict:
    """Create an item and return the response data."""
    response = await client.post("/api/v1/items", json=sample_item_data)
    assert response.status_code == 201
    return response.json()
```

## Create Test Files

### tests/api/__init__.py

```python
# Empty file
```

### tests/api/v1/__init__.py

```python
# Empty file
```

### tests/api/v1/test_items.py

Create `tests/api/v1/test_items.py`:

```python
import pytest
from httpx import AsyncClient


class TestCreateItem:
    """Tests for POST /api/v1/items"""

    async def test_create_item_success(
        self,
        client: AsyncClient,
        sample_item_data: dict,
    ) -> None:
        """Test successful item creation."""
        response = await client.post("/api/v1/items", json=sample_item_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_item_data["name"]
        assert data["description"] == sample_item_data["description"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_item_duplicate_name(
        self,
        client: AsyncClient,
        created_item: dict,
        sample_item_data: dict,
    ) -> None:
        """Test that creating item with duplicate name fails."""
        response = await client.post("/api/v1/items", json=sample_item_data)

        assert response.status_code == 409
        data = response.json()
        assert data["error_code"] == "CONFLICT"

    async def test_create_item_missing_name(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that name is required."""
        response = await client.post("/api/v1/items", json={"description": "test"})

        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"

    async def test_create_item_empty_name(
        self,
        client: AsyncClient,
    ) -> None:
        """Test that empty name is rejected."""
        response = await client.post("/api/v1/items", json={"name": ""})

        assert response.status_code == 422


class TestGetItem:
    """Tests for GET /api/v1/items/{id}"""

    async def test_get_item_success(
        self,
        client: AsyncClient,
        created_item: dict,
    ) -> None:
        """Test successful item retrieval."""
        item_id = created_item["id"]
        response = await client.get(f"/api/v1/items/{item_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_id
        assert data["name"] == created_item["name"]

    async def test_get_item_not_found(
        self,
        client: AsyncClient,
    ) -> None:
        """Test 404 for non-existent item."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/v1/items/{fake_id}")

        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "NOT_FOUND"

    async def test_get_item_invalid_uuid(
        self,
        client: AsyncClient,
    ) -> None:
        """Test 422 for invalid UUID format."""
        response = await client.get("/api/v1/items/not-a-uuid")

        assert response.status_code == 422


class TestListItems:
    """Tests for GET /api/v1/items"""

    async def test_list_items_empty(
        self,
        client: AsyncClient,
    ) -> None:
        """Test listing items when empty."""
        response = await client.get("/api/v1/items")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_items_with_data(
        self,
        client: AsyncClient,
        created_item: dict,
    ) -> None:
        """Test listing items with data."""
        response = await client.get("/api/v1/items")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert data["total"] >= 1

    async def test_list_items_pagination(
        self,
        client: AsyncClient,
        created_item: dict,
    ) -> None:
        """Test pagination parameters."""
        response = await client.get("/api/v1/items?page=1&size=10")

        assert response.status_code == 200
        data = response.json()
        assert "page" in data
        assert "size" in data
        assert data["page"] == 1
        assert data["size"] == 10

    async def test_list_items_filter_by_name(
        self,
        client: AsyncClient,
        created_item: dict,
    ) -> None:
        """Test filtering by name."""
        name = created_item["name"]
        response = await client.get(f"/api/v1/items?name={name}")

        assert response.status_code == 200
        data = response.json()
        assert all(item["name"] == name for item in data["items"])

    async def test_list_items_filter_ilike(
        self,
        client: AsyncClient,
        created_item: dict,
    ) -> None:
        """Test case-insensitive filtering."""
        response = await client.get("/api/v1/items?name__ilike=test")

        assert response.status_code == 200
        data = response.json()
        assert all("test" in item["name"].lower() for item in data["items"])


class TestUpdateItem:
    """Tests for PATCH /api/v1/items/{id}"""

    async def test_update_item_success(
        self,
        client: AsyncClient,
        created_item: dict,
    ) -> None:
        """Test successful item update."""
        item_id = created_item["id"]
        update_data = {"name": "Updated Name"}
        response = await client.patch(f"/api/v1/items/{item_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == created_item["description"]  # Unchanged

    async def test_update_item_partial(
        self,
        client: AsyncClient,
        created_item: dict,
    ) -> None:
        """Test partial update (only description)."""
        item_id = created_item["id"]
        update_data = {"description": "New description"}
        response = await client.patch(f"/api/v1/items/{item_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == created_item["name"]  # Unchanged
        assert data["description"] == "New description"

    async def test_update_item_not_found(
        self,
        client: AsyncClient,
    ) -> None:
        """Test update non-existent item."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.patch(f"/api/v1/items/{fake_id}", json={"name": "test"})

        assert response.status_code == 404


class TestDeleteItem:
    """Tests for DELETE /api/v1/items/{id}"""

    async def test_delete_item_success(
        self,
        client: AsyncClient,
        created_item: dict,
    ) -> None:
        """Test successful item deletion (soft delete)."""
        item_id = created_item["id"]
        response = await client.delete(f"/api/v1/items/{item_id}")

        assert response.status_code == 204

        # Verify item is no longer accessible
        get_response = await client.get(f"/api/v1/items/{item_id}")
        assert get_response.status_code == 404

    async def test_delete_item_not_found(
        self,
        client: AsyncClient,
    ) -> None:
        """Test delete non-existent item."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.delete(f"/api/v1/items/{fake_id}")

        assert response.status_code == 404


class TestRestoreItem:
    """Tests for POST /api/v1/items/{id}/restore"""

    async def test_restore_item_success(
        self,
        client: AsyncClient,
        created_item: dict,
    ) -> None:
        """Test restoring a soft-deleted item."""
        item_id = created_item["id"]

        # Delete the item
        await client.delete(f"/api/v1/items/{item_id}")

        # Restore the item
        response = await client.post(f"/api/v1/items/{item_id}/restore")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_id

        # Verify item is accessible again
        get_response = await client.get(f"/api/v1/items/{item_id}")
        assert get_response.status_code == 200
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/api/v1/test_items.py

# Run specific test class
uv run pytest tests/api/v1/test_items.py::TestCreateItem

# Run specific test
uv run pytest tests/api/v1/test_items.py::TestCreateItem::test_create_item_success

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run tests matching a pattern
uv run pytest -k "create"
```

## Additional Test Fixtures

### Factory Fixtures

```python
@pytest.fixture
def item_factory():
    """Factory for creating item data with unique names."""
    counter = 0

    def _factory(**overrides):
        nonlocal counter
        counter += 1
        defaults = {
            "name": f"Item {counter}",
            "description": f"Description {counter}",
        }
        defaults.update(overrides)
        return defaults

    return _factory


async def test_with_factory(client: AsyncClient, item_factory):
    """Test using factory fixture."""
    item1 = await client.post("/api/v1/items", json=item_factory())
    item2 = await client.post("/api/v1/items", json=item_factory())
    
    assert item1.json()["name"] != item2.json()["name"]
```

### Multiple Items Fixture

```python
@pytest.fixture
async def multiple_items(
    client: AsyncClient,
    item_factory,
) -> list[dict]:
    """Create multiple items for testing."""
    items = []
    for i in range(5):
        response = await client.post("/api/v1/items", json=item_factory())
        items.append(response.json())
    return items
```

## Test Database Setup

Before running tests, create the test database:

```bash
# PostgreSQL
createdb dbname_test

# Or via psql
psql -c "CREATE DATABASE dbname_test;"
```

## Testing Best Practices

1. **Test isolation**: Each test should be independent
2. **Use fixtures**: Share setup code via fixtures
3. **Test edge cases**: Empty data, invalid input, not found
4. **Test error responses**: Verify error codes and messages
5. **Descriptive names**: Test names should describe the scenario
6. **One assertion focus**: Each test should focus on one behavior
