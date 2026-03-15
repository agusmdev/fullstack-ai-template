"""Tests for database base module."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import MetaData

from app.database.base import Base, _convert_url_to_async


class TestConvertUrlToAsync:
    """Tests for _convert_url_to_async function."""

    def test_converts_postgres_url(self):
        result = _convert_url_to_async("postgres://user:pass@host/db")
        assert result == "postgresql+asyncpg://user:pass@host/db"

    def test_converts_postgresql_url(self):
        result = _convert_url_to_async("postgresql://user:pass@host/db")
        assert result == "postgresql+asyncpg://user:pass@host/db"

    def test_converts_sqlite_url(self):
        result = _convert_url_to_async("sqlite:///./local.db")
        assert result == "sqlite+aiosqlite:///./local.db"

    def test_returns_unknown_url_unchanged(self):
        url = "mysql://user:pass@host/db"
        result = _convert_url_to_async(url)
        assert result == url

    def test_does_not_double_convert_postgresql_asyncpg(self):
        url = "postgresql+asyncpg://user:pass@host/db"
        # Already async, should not double-convert
        result = _convert_url_to_async(url)
        # Since it doesn't start with "postgresql://", it passes through
        assert "asyncpg" in result

    def test_sqlite_memory_url(self):
        result = _convert_url_to_async("sqlite:///:memory:")
        assert result == "sqlite+aiosqlite:///:memory:"


class TestBase:
    """Tests for Base declarative base."""

    def test_has_metadata(self):
        assert isinstance(Base.metadata, MetaData)

    def test_naming_conventions(self):
        conventions = Base.metadata.naming_convention
        assert "ix" in conventions
        assert "uq" in conventions
        assert "ck" in conventions
        assert "fk" in conventions
        assert "pk" in conventions

    def test_display_name_uses_tablename(self):
        class MockModel(Base):
            __tablename__ = "mock_items"
            __abstract__ = True

        assert MockModel._display_name() == "Mock_items"
