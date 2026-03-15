"""Tests for database mixins module."""

from datetime import UTC, datetime

import pytest

from app.database.mixins import OrmBaseModel, StrEnum, TimestampOrmBaseModel, JsonOrmBaseModel


class TestOrmBaseModel:
    """Tests for OrmBaseModel Pydantic base."""

    def test_can_instantiate(self):
        model = OrmBaseModel()
        assert model is not None

    def test_from_attributes_config(self):
        assert OrmBaseModel.model_config.get("from_attributes") is True

    def test_from_orm_object(self):
        class FakeOrmObj:
            pass

        obj = FakeOrmObj()
        # from_attributes=True allows model_validate with arbitrary objects
        model = OrmBaseModel.model_validate(obj)
        assert model is not None


class TestStrEnum:
    """Tests for StrEnum class."""

    def test_str_returns_value(self):
        class Color(StrEnum):
            RED = "red"
            BLUE = "blue"

        assert str(Color.RED) == "red"
        assert str(Color.BLUE) == "blue"

    def test_list_returns_all_values(self):
        class Status(StrEnum):
            ACTIVE = "active"
            INACTIVE = "inactive"
            PENDING = "pending"

        result = Status.list()
        assert set(result) == {"active", "inactive", "pending"}

    def test_list_order_matches_definition(self):
        class Direction(StrEnum):
            NORTH = "north"
            SOUTH = "south"
            EAST = "east"
            WEST = "west"

        result = Direction.list()
        assert result == ["north", "south", "east", "west"]

    def test_is_string(self):
        class Priority(StrEnum):
            HIGH = "high"

        assert isinstance(Priority.HIGH, str)
        assert Priority.HIGH == "high"

    def test_comparison_with_string(self):
        class Status(StrEnum):
            ACTIVE = "active"

        assert Status.ACTIVE == "active"


class TestTimestampOrmBaseModel:
    """Tests for TimestampOrmBaseModel."""

    def test_has_created_at_and_updated_at(self):
        now = datetime.now(tz=UTC)
        model = TimestampOrmBaseModel(created_at=now, updated_at=now)
        assert model.created_at == now
        assert model.updated_at == now

    def test_inherits_from_orm_base(self):
        assert issubclass(TimestampOrmBaseModel, OrmBaseModel)


class TestJsonOrmBaseModel:
    """Tests for JsonOrmBaseModel."""

    def test_default_empty_updates_metadata(self):
        model = JsonOrmBaseModel()
        assert model.updates_metadata == {}

    def test_inherits_from_orm_base(self):
        assert issubclass(JsonOrmBaseModel, OrmBaseModel)
