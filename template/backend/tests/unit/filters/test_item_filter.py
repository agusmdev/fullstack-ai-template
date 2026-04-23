"""Tests for ItemFilter."""


from app.modules.items.filters import ItemFilter
from app.modules.items.models import Item


class TestItemFilterConstants:
    """Tests for ItemFilter Constants class."""

    def test_model_is_item(self):
        """Test that the filter is configured for Item model."""
        assert ItemFilter.Constants.model is Item

    def test_search_model_fields(self):
        """Test that search fields are configured correctly."""
        expected_fields = ["name", "description"]
        assert ItemFilter.Constants.search_model_fields == expected_fields


class TestItemFilterFields:
    """Tests for ItemFilter fields."""

    def test_search_field_exists(self):
        """Test that search field exists in model_fields."""
        assert "search" in ItemFilter.model_fields

    def test_search_field_optional(self):
        """Test that search field is optional."""
        filter_instance = ItemFilter()
        assert filter_instance.search is None

    def test_search_field_can_be_set(self):
        """Test that search field can be set."""
        filter_instance = ItemFilter(search="test")
        assert filter_instance.search == "test"


class TestItemFilterInheritance:
    """Tests for ItemFilter inheritance."""

    def test_inherits_from_filter(self):
        """Test that ItemFilter inherits from Filter."""
        from fastapi_filter.contrib.sqlalchemy.filter import Filter

        assert issubclass(ItemFilter, Filter)

    def test_has_filter_method(self):
        """Test that ItemFilter has filter method from parent."""
        filter_instance = ItemFilter()
        assert hasattr(filter_instance, "filter")
        assert callable(filter_instance.filter)


class TestItemFilterInstantiation:
    """Tests for ItemFilter instantiation."""

    def test_create_empty_filter(self):
        """Test creating filter with no parameters."""
        filter_instance = ItemFilter()
        assert filter_instance.search is None

    def test_create_with_search(self):
        """Test creating filter with search parameter."""
        filter_instance = ItemFilter(search="laptop")
        assert filter_instance.search == "laptop"

    def test_filter_is_pydantic_model(self):
        """Test that filter is a Pydantic model."""

        filter_instance = ItemFilter()
        assert hasattr(filter_instance, "model_dump")
