"""Tests for database mixins module."""

from datetime import UTC, datetime

import pytest

from app.database.mixins import OrmBaseModel, TimestampOrmBaseModel, JsonOrmBaseModel


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
