"""
Integration test configuration and fixtures.

This module provides test fixtures and configuration for integration tests,
with PostgreSQL testcontainers support for database testing.
"""

import sys
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient


# Configure loguru for testing before any imports that use it
def _configure_test_logger():
    """Configure loguru for test environment."""
    from loguru import logger

    # Remove default handler and add a simple one for tests
    logger.remove()
    logger.add(
        sys.stderr,
        level="DEBUG",
        format="{level}: {message}",
        colorize=False,
    )


_configure_test_logger()

from app.main import create_app


@pytest.fixture(scope="session")
def app():
    """Creates the FastAPI app with test configuration."""
    # Create app without Sentry for testing
    test_app = create_app(add_sentry=False)

    # Override authentication to skip Firebase
    def mock_user_id():
        return "test-user-id"

    def mock_user_email():
        return "test@example.com"

    from app.user.auth.permissions import AuthenticatedUser

    test_app.dependency_overrides[AuthenticatedUser.current_user_id] = mock_user_id
    test_app.dependency_overrides[AuthenticatedUser.current_user_email] = mock_user_email

    return test_app


@pytest.fixture(scope="function")
def client(app):
    """Creates a test client for the FastAPI app."""
    # Mock the middleware logger to avoid any issues during request processing
    mock_logger = MagicMock()
    mock_logger.info = MagicMock()
    mock_logger.warning = MagicMock()
    mock_logger.error = MagicMock()
    mock_logger.debug = MagicMock()
    mock_logger.log = MagicMock()
    mock_logger.bind = MagicMock(return_value=mock_logger)
    mock_logger.opt = MagicMock(return_value=mock_logger)

    with patch("app.core.logging.middleware.logger", mock_logger):
        with TestClient(app=app, base_url="http://test") as test_client:
            yield test_client


@pytest.fixture(scope="function")
def authorized_client(client):
    """Returns a test client with authorization headers."""
    # Add a dummy authorization header
    client.headers.update({"Authorization": "Bearer test-token"})
    return client


@pytest.fixture
def sample_text_file():
    """Returns a simple text file for testing."""
    content = b"Sample text content for testing"

    class MockFile:
        def __init__(self, filename: str, content: bytes):
            self.filename = filename
            self.file = BytesIO(content)
            self.content_type = "text/plain"

        def read(self):
            current_pos = self.file.tell()
            self.file.seek(0)
            content = self.file.read()
            self.file.seek(current_pos)
            return content

    return MockFile("test_file.txt", content)


# PostgreSQL testcontainers support (optional - requires testcontainers[postgres])
try:
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
    from testcontainers.postgres import PostgresContainer

    from app.database.base import Base

    @pytest.fixture(scope="session")
    def postgres_container():
        """Start a PostgreSQL container for the test session."""
        with PostgresContainer("postgres:16-alpine") as postgres:
            yield postgres

    @pytest.fixture(scope="session")
    def db_url(postgres_container):
        """Get the database URL from the container."""
        # Convert psycopg2 URL to asyncpg
        url = postgres_container.get_connection_url()
        return url.replace("psycopg2", "asyncpg")

    @pytest.fixture(scope="session")
    async def async_engine(db_url):
        """Create async engine and initialize database schema."""
        engine = create_async_engine(db_url, echo=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield engine

        await engine.dispose()

    @pytest.fixture
    async def db_session(async_engine):
        """Create a database session for each test."""
        session_factory = async_sessionmaker(
            bind=async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        async with session_factory() as session:
            yield session
            await session.rollback()

    @pytest.fixture
    def app_with_db(app, db_session):
        """App with database session override."""
        from app.dependencies import get_db_session

        async def override_get_db_session():
            yield db_session

        app.dependency_overrides[get_db_session] = override_get_db_session
        yield app
        # Clean up override
        del app.dependency_overrides[get_db_session]

    @pytest.fixture
    async def async_client(app_with_db):
        """Async client for testing with database."""
        mock_logger = MagicMock()
        mock_logger.info = MagicMock()
        mock_logger.warning = MagicMock()
        mock_logger.error = MagicMock()
        mock_logger.debug = MagicMock()
        mock_logger.log = MagicMock()
        mock_logger.bind = MagicMock(return_value=mock_logger)
        mock_logger.opt = MagicMock(return_value=mock_logger)

        with patch("app.core.logging.middleware.logger", mock_logger):
            async with AsyncClient(
                transport=ASGITransport(app=app_with_db),
                base_url="http://test",
            ) as client:
                yield client

except ImportError:
    # testcontainers not installed - skip database fixtures
    pass
