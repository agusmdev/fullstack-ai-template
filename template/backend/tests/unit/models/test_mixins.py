"""Tests for database mixins module."""

from app.database.mixins import OrmBaseModel


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
