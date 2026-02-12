"""Tests for UserFilter."""

import pytest

from app.user.filters import UserFilter
from app.user.models import User


class TestUserFilterConstants:
    """Tests for UserFilter Constants class."""

    def test_model_is_user(self):
        """Test that the filter is configured for User model."""
        assert UserFilter.Constants.model is User

    def test_search_model_fields(self):
        """Test that search fields are configured correctly."""
        expected_fields = ["email", "first_name", "last_name", "full_name"]
        assert UserFilter.Constants.search_model_fields == expected_fields

    def test_search_field_name(self):
        """Test that search field name is configured."""
        assert UserFilter.Constants.search_field_name == "search"


class TestUserFilterFields:
    """Tests for UserFilter fields."""

    def test_search_field_exists(self):
        """Test that search field exists in model_fields."""
        assert "search" in UserFilter.model_fields

    def test_email_field_exists(self):
        """Test that email field exists in model_fields."""
        assert "email" in UserFilter.model_fields

    def test_order_by_field_exists(self):
        """Test that order_by field exists in model_fields."""
        assert "order_by" in UserFilter.model_fields

    def test_default_order_by(self):
        """Test default order_by value."""
        filter_instance = UserFilter()
        assert filter_instance.order_by == ["created_at"]

    def test_search_field_optional(self):
        """Test that search field is optional."""
        filter_instance = UserFilter()
        assert filter_instance.search is None

    def test_email_field_optional(self):
        """Test that email field is optional."""
        filter_instance = UserFilter()
        assert filter_instance.email is None


class TestUserFilterInheritance:
    """Tests for UserFilter inheritance."""

    def test_inherits_from_filter(self):
        """Test that UserFilter inherits from Filter."""
        from fastapi_filter.contrib.sqlalchemy import Filter

        assert issubclass(UserFilter, Filter)

    def test_has_filter_method(self):
        """Test that UserFilter has filter method from parent."""
        filter_instance = UserFilter()
        assert hasattr(filter_instance, "filter")


class TestUserFilterInstantiation:
    """Tests for UserFilter instantiation."""

    def test_create_empty_filter(self):
        """Test creating filter with no parameters."""
        filter_instance = UserFilter()
        assert filter_instance.search is None
        assert filter_instance.email is None

    def test_create_with_email(self):
        """Test creating filter with email parameter."""
        filter_instance = UserFilter(email="test@example.com")
        assert filter_instance.email == "test@example.com"

    def test_create_with_search(self):
        """Test creating filter with search parameter."""
        filter_instance = UserFilter(search="john")
        assert filter_instance.search == "john"

    def test_create_with_custom_order_by(self):
        """Test creating filter with custom order_by."""
        filter_instance = UserFilter(order_by=["email", "created_at"])
        assert filter_instance.order_by == ["email", "created_at"]
