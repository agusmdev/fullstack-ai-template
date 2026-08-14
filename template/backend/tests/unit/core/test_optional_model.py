"""Tests for optional_model decorator and utilities."""

import pytest
from pydantic import BaseModel, Field, ValidationError

from app.core.optional_model import partial_model


class SimpleModel(BaseModel):
    """Simple model for testing."""

    name: str
    value: int
    description: str | None = None


class TestPartialModel:
    """Tests for partial_model decorator."""

    def test_all_fields_become_optional(self):
        """Test that all fields become optional with default None."""
        PartialSimple = partial_model(SimpleModel)

        # Should be able to instantiate with no arguments
        instance = PartialSimple()
        assert instance.name is None
        assert instance.value is None
        assert instance.description is None

    def test_can_still_set_values(self):
        """Test that values can still be set."""
        PartialSimple = partial_model(SimpleModel)

        instance = PartialSimple(name="test", value=42)
        assert instance.name == "test"
        assert instance.value == 42
        assert instance.description is None

    def test_partial_instantiation(self):
        """Test partial instantiation with only some fields."""
        PartialSimple = partial_model(SimpleModel)

        instance = PartialSimple(name="only name")
        assert instance.name == "only name"
        assert instance.value is None

    def test_model_name_prefixed(self):
        """Test that partial model name is prefixed with 'Partial'."""
        PartialSimple = partial_model(SimpleModel)
        assert PartialSimple.__name__ == "PartialSimpleModel"

    def test_preserves_module(self):
        """Test that module is preserved."""
        PartialSimple = partial_model(SimpleModel)
        assert PartialSimple.__module__ == SimpleModel.__module__

    def test_original_model_unchanged(self):
        """Test that original model is not modified."""
        _ = partial_model(SimpleModel)

        # Original should still require name and value
        with pytest.raises(ValidationError):
            SimpleModel()


class TestPartialModelWithFieldConstraints:
    """Tests for partial models with field constraints."""

    def test_preserves_field_info(self):
        """Test that Field info is preserved (except defaults)."""

        class ConstrainedModel(BaseModel):
            name: str = Field(min_length=3, max_length=50)
            value: int = Field(ge=0, le=100)

        PartialConstrained = partial_model(ConstrainedModel)

        # Should accept None
        instance = PartialConstrained()
        assert instance.name is None

        # Should still validate when value provided
        instance = PartialConstrained(name="test")
        assert instance.name == "test"
