"""Unit test configuration and fixtures."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session():
    """Create a mock async database session for unit tests."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": uuid.UUID("12345678-1234-5678-1234-567812345678"),
        "email": "test@example.com",
        "display_name": "Test User",
        "is_active": True,
        "password": None,
        "email_verified_at": None,
        "created_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        "updated_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    }
