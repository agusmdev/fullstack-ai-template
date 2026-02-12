"""Tests for ItemRepository."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.items.repository import ItemRepository


class TestItemRepositoryModel:
    """Tests for ItemRepository model attribute."""

    def test_model_is_item(self, mock_session):
        """Test that model is set to Item."""
        from app.modules.items.models import Item

        repo = ItemRepository(session=mock_session)

        assert repo.model is Item


class TestItemRepositoryInheritance:
    """Tests for ItemRepository inheritance from SQLAlchemyRepository."""

    def test_inherits_from_sqlalchemy_repository(self):
        """Test that ItemRepository inherits from SQLAlchemyRepository."""
        from app.repositories.sql_repository import SQLAlchemyRepository

        assert issubclass(ItemRepository, SQLAlchemyRepository)

    def test_has_crud_methods(self, mock_session):
        """Test that repository has all CRUD methods."""
        repo = ItemRepository(session=mock_session)

        assert hasattr(repo, "get")
        assert hasattr(repo, "get_all")
        assert hasattr(repo, "create")
        assert hasattr(repo, "update")
        assert hasattr(repo, "delete")
        assert hasattr(repo, "create_many")
        assert hasattr(repo, "upsert")


class TestItemRepositoryInit:
    """Tests for ItemRepository initialization."""

    def test_init_sets_session(self, mock_session):
        """Test that session is set on initialization."""
        repo = ItemRepository(session=mock_session)

        assert repo._session == mock_session

    def test_init_creates_query_builder(self, mock_session):
        """Test that query builder is created on initialization."""
        repo = ItemRepository(session=mock_session)

        assert repo._query_builder is not None
