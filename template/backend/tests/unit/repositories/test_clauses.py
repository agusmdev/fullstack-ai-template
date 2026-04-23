"""Tests for repository ON CONFLICT clauses."""

from unittest.mock import MagicMock

from app.repositories.clauses import (
    conflict_do_nothing,
    conflict_do_update,
    conflict_passthrough,
)


class TestConflictDoNothing:
    """Tests for conflict_do_nothing clause."""

    def test_returns_insert_with_on_conflict_do_nothing(self):
        """Test that on_conflict_do_nothing is called on insert."""
        mock_insert = MagicMock()
        mock_insert.on_conflict_do_nothing.return_value = mock_insert

        result = conflict_do_nothing(mock_insert)

        mock_insert.on_conflict_do_nothing.assert_called_once_with()
        assert result == mock_insert

    def test_passes_kwargs_to_on_conflict_do_nothing(self):
        """Test that kwargs are passed through."""
        mock_insert = MagicMock()
        mock_insert.on_conflict_do_nothing.return_value = mock_insert

        result = conflict_do_nothing(mock_insert, index_elements=["id"])

        mock_insert.on_conflict_do_nothing.assert_called_once_with(index_elements=["id"])


class TestConflictDoUpdate:
    """Tests for conflict_do_update clause."""

    def test_returns_insert_with_on_conflict_do_update(self):
        """Test that on_conflict_do_update is called on insert."""
        mock_insert = MagicMock()
        mock_insert.on_conflict_do_update.return_value = mock_insert

        result = conflict_do_update(mock_insert)

        mock_insert.on_conflict_do_update.assert_called_once_with()
        assert result == mock_insert

    def test_passes_kwargs_to_on_conflict_do_update(self):
        """Test that kwargs are passed through."""
        mock_insert = MagicMock()
        mock_insert.on_conflict_do_update.return_value = mock_insert

        result = conflict_do_update(
            mock_insert, index_elements=["id"], set_={"name": "updated"}
        )

        mock_insert.on_conflict_do_update.assert_called_once_with(
            index_elements=["id"], set_={"name": "updated"}
        )


class TestConflictPassthrough:
    """Tests for conflict_passthrough clause."""

    def test_returns_insert_unchanged(self):
        """Test that insert is returned without modification."""
        mock_insert = MagicMock()

        result = conflict_passthrough(mock_insert)

        assert result == mock_insert
        # Should not call any on_conflict methods
        mock_insert.on_conflict_do_nothing.assert_not_called()
        mock_insert.on_conflict_do_update.assert_not_called()


class TestClausesAreCallable:
    """Tests that all clauses are properly callable."""

    def test_all_clauses_are_callable(self):
        """Test that all clause functions are callable."""
        assert callable(conflict_do_nothing)
        assert callable(conflict_do_update)
        assert callable(conflict_passthrough)

    def test_clauses_return_insert(self):
        """Test that all clauses return the insert statement."""
        mock_insert = MagicMock()
        mock_insert.on_conflict_do_nothing.return_value = mock_insert
        mock_insert.on_conflict_do_update.return_value = mock_insert

        assert conflict_do_nothing(mock_insert) == mock_insert
        assert conflict_do_update(mock_insert) == mock_insert
        assert conflict_passthrough(mock_insert) == mock_insert
