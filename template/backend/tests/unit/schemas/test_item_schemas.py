"""Tests for item schemas."""

import uuid

import pytest
from pydantic import ValidationError

from app.modules.items.schemas import ItemBase, ItemCreate, ItemResponse, ItemUpdate


class TestItemBase:
    """Tests for ItemBase schema."""

    def test_valid_item(self):
        """Test creating a valid item."""
        item = ItemBase(name="Test Item", description="A test item")
        assert item.name == "Test Item"
        assert item.description == "A test item"

    def test_minimal_item(self):
        """Test creating item with minimal required fields."""
        item = ItemBase(name="Test")
        assert item.name == "Test"
        assert item.description is None

    def test_name_required(self):
        """Test that name is required."""
        with pytest.raises(ValidationError) as exc_info:
            ItemBase()
        assert "name" in str(exc_info.value)

    def test_name_min_length(self):
        """Test name minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            ItemBase(name="")
        assert "name" in str(exc_info.value)

    def test_name_max_length(self):
        """Test name maximum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            ItemBase(name="a" * 256)
        assert "name" in str(exc_info.value)

    def test_description_max_length(self):
        """Test description maximum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            ItemBase(name="Test", description="a" * 5001)
        assert "description" in str(exc_info.value)


class TestItemCreate:
    """Tests for ItemCreate schema."""

    def test_inherits_from_item_base(self):
        """Test that ItemCreate inherits from ItemBase."""
        assert issubclass(ItemCreate, ItemBase)

    def test_create_item(self):
        """Test creating an item for creation."""
        item = ItemCreate(name="New Item")
        assert item.name == "New Item"


class TestItemUpdate:
    """Tests for ItemUpdate schema (partial model)."""

    def test_all_fields_optional(self):
        """Test that all fields are optional for updates."""
        item = ItemUpdate()
        assert item.name is None
        assert item.description is None

    def test_partial_update(self):
        """Test partial update with only some fields."""
        item = ItemUpdate(name="Updated Name")
        assert item.name == "Updated Name"

    def test_full_update(self):
        """Test update with all fields."""
        item = ItemUpdate(name="Full Update", description="New desc")
        assert item.name == "Full Update"
        assert item.description == "New desc"


class TestItemResponse:
    """Tests for ItemResponse schema."""

    def test_includes_id(self):
        """Test that response includes id field."""
        user_id = uuid.uuid4()
        item = ItemResponse(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            user_id=user_id,
            name="Test Item",
        )
        assert item.id == uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert item.user_id == user_id

    def test_from_attributes_mode(self):
        """Test that model has from_attributes config for ORM mode."""
        assert ItemResponse.model_config.get("from_attributes") is True

    def test_full_response(self):
        """Test full response with all fields."""
        item_id = uuid.uuid4()
        user_id = uuid.uuid4()
        item = ItemResponse(
            id=item_id,
            user_id=user_id,
            name="Complete Item",
            description="Full description",
        )
        assert item.id == item_id
        assert item.user_id == user_id
        assert item.name == "Complete Item"
        assert item.description == "Full description"

    def test_json_serialization(self):
        """Test JSON serialization of response."""
        item_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user_id = uuid.uuid4()
        item = ItemResponse(id=item_id, user_id=user_id, name="Test")
        json_data = item.model_dump_json()
        assert "12345678-1234-5678-1234-567812345678" in json_data
        assert "Test" in json_data
