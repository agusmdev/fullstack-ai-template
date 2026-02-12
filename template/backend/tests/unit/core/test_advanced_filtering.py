"""Tests for advanced filtering utilities."""

import pytest

from app.core.advanced_filtering import (
    _backward_compatible_value_for_like_and_ilike,
    _orm_operator_transformer,
)


class TestBackwardCompatibleLikeValue:
    """Tests for _backward_compatible_value_for_like_and_ilike function."""

    def test_adds_percent_signs_when_missing(self):
        """Test that % signs are added when not present."""
        result = _backward_compatible_value_for_like_and_ilike("test")
        assert result == "%test%"

    def test_preserves_existing_percent_at_start(self):
        """Test that existing % at start is preserved."""
        result = _backward_compatible_value_for_like_and_ilike("%test")
        assert result == "%test"

    def test_preserves_existing_percent_at_end(self):
        """Test that existing % at end is preserved."""
        result = _backward_compatible_value_for_like_and_ilike("test%")
        assert result == "test%"

    def test_preserves_existing_percent_both_sides(self):
        """Test that existing % on both sides is preserved."""
        result = _backward_compatible_value_for_like_and_ilike("%test%")
        assert result == "%test%"

    def test_preserves_percent_in_middle(self):
        """Test that % in middle is preserved."""
        result = _backward_compatible_value_for_like_and_ilike("te%st")
        assert result == "te%st"

    def test_empty_string(self):
        """Test with empty string."""
        result = _backward_compatible_value_for_like_and_ilike("")
        assert result == "%%"


class TestOrmOperatorTransformer:
    """Tests for _orm_operator_transformer dictionary."""

    def test_neq_operator(self):
        """Test neq (not equal) operator."""
        operator, value = _orm_operator_transformer["neq"]("test")
        assert operator == "__ne__"
        assert value == "test"

    def test_gt_operator(self):
        """Test gt (greater than) operator."""
        operator, value = _orm_operator_transformer["gt"](10)
        assert operator == "__gt__"
        assert value == 10

    def test_gte_operator(self):
        """Test gte (greater than or equal) operator."""
        operator, value = _orm_operator_transformer["gte"](10)
        assert operator == "__ge__"
        assert value == 10

    def test_lt_operator(self):
        """Test lt (less than) operator."""
        operator, value = _orm_operator_transformer["lt"](10)
        assert operator == "__lt__"
        assert value == 10

    def test_lte_operator(self):
        """Test lte (less than or equal) operator."""
        operator, value = _orm_operator_transformer["lte"](10)
        assert operator == "__le__"
        assert value == 10

    def test_in_operator(self):
        """Test in operator."""
        operator, value = _orm_operator_transformer["in"]([1, 2, 3])
        assert operator == "in_"
        assert value == [1, 2, 3]

    def test_not_in_operator(self):
        """Test not_in operator."""
        operator, value = _orm_operator_transformer["not_in"]([1, 2, 3])
        assert operator == "not_in"
        assert value == [1, 2, 3]

    def test_isnull_true(self):
        """Test isnull with True value."""
        operator, value = _orm_operator_transformer["isnull"](True)
        assert operator == "is_"
        assert value is None

    def test_isnull_false(self):
        """Test isnull with False value."""
        operator, value = _orm_operator_transformer["isnull"](False)
        assert operator == "is_not"
        assert value is None

    def test_like_operator(self):
        """Test like operator."""
        operator, value = _orm_operator_transformer["like"]("test")
        assert operator == "like"
        assert value == "%test%"

    def test_like_operator_with_percent(self):
        """Test like operator with existing percent sign."""
        operator, value = _orm_operator_transformer["like"]("%test%")
        assert operator == "like"
        assert value == "%test%"

    def test_ilike_operator(self):
        """Test ilike operator."""
        operator, value = _orm_operator_transformer["ilike"]("test")
        assert operator == "ilike"
        assert value == "%test%"

    def test_ilike_operator_with_percent(self):
        """Test ilike operator with existing percent sign."""
        operator, value = _orm_operator_transformer["ilike"]("test%")
        assert operator == "ilike"
        assert value == "test%"

    def test_not_operator(self):
        """Test not operator."""
        operator, value = _orm_operator_transformer["not"]("test")
        assert operator == "is_not"
        assert value == "test"

    def test_all_operators_exist(self):
        """Test that all expected operators are defined."""
        expected_operators = [
            "neq",
            "gt",
            "gte",
            "lt",
            "lte",
            "in",
            "not_in",
            "isnull",
            "like",
            "ilike",
            "not",
        ]
        for op in expected_operators:
            assert op in _orm_operator_transformer
