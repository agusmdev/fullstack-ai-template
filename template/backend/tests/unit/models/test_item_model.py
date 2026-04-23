"""Tests for Item model."""

import uuid

from app.modules.items.models import Item


class TestItemModel:
    """Tests for Item model class."""

    def test_item_creation(self):
        """Test creating an Item instance."""
        item = Item(
            id=uuid.uuid4(),
            name="Test Item",
            description="A test item",
            quantity=10,
            sku="SKU-001",
        )
        assert item.name == "Test Item"
        assert item.description == "A test item"
        assert item.quantity == 10
        assert item.sku == "SKU-001"

    def test_item_tablename(self):
        """Test that tablename is correctly set."""
        assert Item.__tablename__ == "item"

    def test_item_minimal(self):
        """Test creating item with minimal fields."""
        item = Item(
            id=uuid.uuid4(),
            name="Minimal Item",
        )
        assert item.name == "Minimal Item"


class TestItemDisplayName:
    """Tests for Item._display_name class method."""

    def test_display_name_capitalized(self):
        """Test that _display_name returns capitalized tablename."""
        result = Item._display_name()
        assert result == "Item"

    def test_display_name_is_string(self):
        """Test that _display_name returns a string."""
        result = Item._display_name()
        assert isinstance(result, str)


class TestItemDefaults:
    """Tests for Item model default values."""

    def test_quantity_default(self):
        """Test that quantity defaults to 0."""
        item = Item(id=uuid.uuid4(), name="Test")
        # Check default from column definition
        assert Item.quantity.default.arg == 0

    def test_description_nullable(self):
        """Test that description is nullable."""
        item = Item(id=uuid.uuid4(), name="Test", description=None)
        assert item.description is None

    def test_sku_nullable(self):
        """Test that sku is nullable."""
        item = Item(id=uuid.uuid4(), name="Test", sku=None)
        assert item.sku is None


class TestItemColumnConstraints:
    """Tests for Item model column constraints."""

    def test_name_max_length(self):
        """Test that name has max length of 255."""
        # Get the column type
        name_column = Item.__table__.c.name
        assert name_column.type.length == 255

    def test_sku_max_length(self):
        """Test that sku has max length of 100."""
        sku_column = Item.__table__.c.sku
        assert sku_column.type.length == 100

    def test_sku_unique(self):
        """Test that sku has unique constraint."""
        sku_column = Item.__table__.c.sku
        assert sku_column.unique is True

    def test_sku_indexed(self):
        """Test that sku is indexed."""
        sku_column = Item.__table__.c.sku
        assert sku_column.index is True
