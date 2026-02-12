"""Tests for repository exceptions."""

import pytest

from app.repositories.exceptions import (
    DuplicateError,
    NotFoundError,
    ReferencedError,
    RepositoryError,
)


class TestRepositoryError:
    """Tests for the base RepositoryError class."""

    def test_default_values(self):
        """Test default values for RepositoryError."""
        exc = RepositoryError()
        assert exc.status_code == 500
        assert exc.detail == "Repository error"
        assert RepositoryError.error_code == "repository_error"

    def test_custom_detail(self):
        """Test custom detail message."""
        exc = RepositoryError(detail="Custom repo error")
        assert exc.detail == "Custom repo error"


class TestNotFoundError:
    """Tests for NotFoundError exception."""

    def test_default_values(self):
        """Test default values for NotFoundError."""
        exc = NotFoundError()
        assert exc.status_code == 404
        assert exc.detail == "Item not found"
        assert NotFoundError.error_code == "not_found"

    def test_custom_detail(self):
        """Test custom detail for not found."""
        exc = NotFoundError(detail="User with ID 123 not found")
        assert exc.detail == "User with ID 123 not found"
        assert exc.status_code == 404

    def test_is_raiseable(self):
        """Test that NotFoundError can be raised and caught."""
        with pytest.raises(NotFoundError) as exc_info:
            raise NotFoundError(detail="Entity not found")
        assert exc_info.value.status_code == 404


class TestDuplicateError:
    """Tests for DuplicateError exception."""

    def test_default_values(self):
        """Test default values for DuplicateError."""
        exc = DuplicateError()
        assert exc.status_code == 400
        assert exc.detail == "Item already exists"
        assert DuplicateError.error_code == "duplicate_item"

    def test_custom_detail(self):
        """Test custom detail for duplicate."""
        exc = DuplicateError(detail="Email already registered")
        assert exc.detail == "Email already registered"
        assert exc.status_code == 400


class TestReferencedError:
    """Tests for ReferencedError exception."""

    def test_default_values(self):
        """Test default values for ReferencedError."""
        exc = ReferencedError()
        assert exc.status_code == 400
        assert exc.detail == "Item is referenced by other items"
        assert ReferencedError.error_code == "referenced_item"

    def test_custom_detail(self):
        """Test custom detail for referenced error."""
        exc = ReferencedError(detail="Cannot delete: item has associated orders")
        assert exc.detail == "Cannot delete: item has associated orders"


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_not_found_inherits_from_repository_error(self):
        """Test NotFoundError inherits from RepositoryError."""
        exc = NotFoundError()
        assert isinstance(exc, RepositoryError)

    def test_duplicate_inherits_from_repository_error(self):
        """Test DuplicateError inherits from RepositoryError."""
        exc = DuplicateError()
        assert isinstance(exc, RepositoryError)

    def test_referenced_inherits_from_repository_error(self):
        """Test ReferencedError inherits from RepositoryError."""
        exc = ReferencedError()
        assert isinstance(exc, RepositoryError)

    def test_catch_all_repository_errors(self):
        """Test that all repo errors can be caught with RepositoryError."""
        for exc_class in [NotFoundError, DuplicateError, ReferencedError]:
            with pytest.raises(RepositoryError):
                raise exc_class()
