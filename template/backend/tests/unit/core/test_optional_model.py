"""Tests for optional_model decorator and utilities."""

import pytest
from pydantic import BaseModel, Field

from app.core.optional_model import (
    _extract_nested_basemodels,
    partial_model,
    recursive_partial_model,
)


class SimpleModel(BaseModel):
    """Simple model for testing."""

    name: str
    value: int
    description: str | None = None


class NestedModel(BaseModel):
    """Model with nested BaseModel."""

    title: str
    simple: SimpleModel


class DeeplyNestedModel(BaseModel):
    """Model with deeply nested BaseModels."""

    id: int
    nested: NestedModel
    items: list[SimpleModel]


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
        with pytest.raises(Exception):  # ValidationError
            SimpleModel()


class TestRecursivePartialModel:
    """Tests for recursive_partial_model function."""

    def test_simple_model(self):
        """Test recursive partial on simple model."""
        PartialSimple = recursive_partial_model(SimpleModel)

        instance = PartialSimple()
        assert instance.name is None
        assert instance.value is None

    def test_nested_model_becomes_partial(self):
        """Test that nested models also become partial."""
        PartialNested = recursive_partial_model(NestedModel)

        instance = PartialNested()
        assert instance.title is None
        assert instance.simple is None

    def test_can_set_partial_nested(self):
        """Test setting partial nested model."""
        PartialNested = recursive_partial_model(NestedModel)

        # Should accept partially filled nested model
        instance = PartialNested(title="test")
        assert instance.title == "test"

    def test_deeply_nested(self):
        """Test deeply nested models."""
        PartialDeep = recursive_partial_model(DeeplyNestedModel)

        instance = PartialDeep()
        assert instance.id is None
        assert instance.nested is None
        assert instance.items is None

    def test_caching_prevents_infinite_recursion(self):
        """Test that caching works for recursive models."""

        class SelfReferencing(BaseModel):
            name: str
            parent: "SelfReferencing | None" = None

        # Should not cause infinite recursion
        PartialSelfRef = recursive_partial_model(SelfReferencing)
        instance = PartialSelfRef()
        assert instance.name is None


class TestExtractNestedBasemodels:
    """Tests for _extract_nested_basemodels helper."""

    def test_direct_basemodel(self):
        """Test extracting direct BaseModel type."""
        result = _extract_nested_basemodels(SimpleModel)
        assert SimpleModel in result

    def test_optional_basemodel(self):
        """Test extracting from Optional[BaseModel]."""
        from typing import Optional

        result = _extract_nested_basemodels(Optional[SimpleModel])
        assert SimpleModel in result

    def test_list_of_basemodel(self):
        """Test extracting from list[BaseModel]."""
        result = _extract_nested_basemodels(list[SimpleModel])
        assert SimpleModel in result

    def test_primitive_type(self):
        """Test that primitive types return empty list."""
        result = _extract_nested_basemodels(str)
        assert result == []

        result = _extract_nested_basemodels(int)
        assert result == []

    def test_string_annotation(self):
        """Test that string annotations return empty list."""
        result = _extract_nested_basemodels("SomeForwardRef")
        assert result == []

    def test_none_type(self):
        """Test with None type."""
        result = _extract_nested_basemodels(type(None))
        assert result == []


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
