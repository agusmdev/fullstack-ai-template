"""Shared test configuration and fixtures."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel


@pytest.fixture
def sample_uuid():
    """Generate a sample UUID for testing."""
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def sample_datetime():
    """Generate a sample datetime for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def mock_async_session():
    """Create a mock async database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


class MockEntity(BaseModel):
    """Mock entity for testing."""

    id: uuid.UUID
    name: str
    value: int = 0


@pytest.fixture
def mock_entity(sample_uuid):
    """Create a mock entity for testing."""
    return MockEntity(id=sample_uuid, name="Test Entity", value=42)
