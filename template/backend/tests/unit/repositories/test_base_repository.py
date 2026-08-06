"""Direct tests for BaseRepository abstract contract and QueryOptions.

These cover the abstract interface declared in app/repositories/base_repository.py,
which is otherwise only exercised transitively through concrete subclasses.
"""

import inspect
import uuid

import pytest
from fastapi_pagination import Params
from pydantic import BaseModel
from sqlalchemy import select

from app.database.base import Base
from app.modules.teams.models import Team
from app.repositories.base_repository import BaseRepository, QueryOptions
from app.repositories.clauses import conflict_passthrough


class TestQueryOptionsDefaults:
    """QueryOptions is the options DTO used by repository read methods."""

    def test_defaults(self):
        opts = QueryOptions()
        assert opts.base_query is None
        assert opts.return_scalars is True
        assert opts.response_model is None
        assert opts.pagination_kwargs == {}

    def test_custom_factory_is_independent_per_instance(self):
        """The mutable pagination_kwargs default must not leak between instances."""
        a = QueryOptions()
        b = QueryOptions()
        a.pagination_kwargs["unique"] = True
        assert b.pagination_kwargs == {}

    def test_carries_base_query(self):
        q = select(Team)
        opts = QueryOptions(
            base_query=q, return_scalars=False, response_model=BaseModel
        )
        assert opts.base_query is q
        assert opts.return_scalars is False
        assert opts.response_model is BaseModel


class TestBaseRepositoryIsAbstract:
    """BaseRepository defines an interface; it must not be instantiable on its own."""

    def test_cannot_instantiate_without_overrides(self):
        with pytest.raises(TypeError):
            BaseRepository()  # type: ignore[abstract]

    def test_concrete_subclass_must_implement_all_abstract_methods(self):
        """A subclass missing even one abstract method remains uninstantiable."""

        class Partial(BaseRepository[Team]):
            async def get(self, entity_id, raise_error=True, response_model=None): ...

        with pytest.raises(TypeError):
            Partial()  # type: ignore[abstract]

    def test_full_subclass_is_instantiable(self):
        """A subclass implementing every abstract method instantiates successfully."""

        class Complete(BaseRepository[Team]):
            model = Team

            async def get(self, entity_id, raise_error=True, response_model=None): ...

            async def get_by_field(
                self, field, value, raise_error=True, response_model=None
            ): ...

            async def get_all(self, entity_filter=None, options=None): ...

            async def get_all_paginated(
                self, pagination_params, entity_filter=None, options=None
            ): ...

            async def create(self, entity, **extra_fields): ...

            async def create_many(self, entities, on_conflict=conflict_passthrough): ...

            async def upsert(self, entity, **extra_fields): ...

            async def update(self, entity_id, updated_entity): ...

            async def delete(self, entity_id): ...

            async def delete_many(self, delete_filter_query): ...

        repo = Complete()
        assert isinstance(repo, BaseRepository)


class TestBaseRepositoryAbstractSurface:
    """The abstract method set is the public repository contract — guard it."""

    @pytest.fixture(scope="class")
    def abstract_methods(self):
        return BaseRepository.__abstractmethods__

    def test_all_crud_methods_are_abstract(self, abstract_methods):
        expected = {
            "get",
            "get_by_field",
            "get_all",
            "get_all_paginated",
            "create",
            "create_many",
            "upsert",
            "update",
            "delete",
            "delete_many",
        }
        assert set(abstract_methods) == expected

    def test_abstract_methods_are_marked_abstract(self):
        """Every contract method exposes the abstract descriptor flag."""
        for name in BaseRepository.__abstractmethods__:
            descriptor = inspect.getattr_static(BaseRepository, name)
            assert getattr(descriptor, "__isabstractmethod__", False), (
                f"{name} should be marked abstract"
            )

    def test_get_signature_contract(self):
        """get() must accept entity_id, raise_error and response_model."""
        sig = inspect.signature(BaseRepository.get)
        params = sig.parameters
        assert "entity_id" in params
        assert "raise_error" in params
        assert "response_model" in params
        assert params["raise_error"].default is True
        assert params["response_model"].default is None

    def test_create_accepts_extra_fields(self):
        """create() passes through arbitrary extra fields (e.g. user_id)."""
        sig = inspect.signature(BaseRepository.create)
        assert any(
            p.kind is inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
        )

    def test_create_many_defaults_to_passthrough(self):
        """create_many() defaults to the conflict-passthrough callable."""
        sig = inspect.signature(BaseRepository.create_many)
        assert sig.parameters["on_conflict"].default is conflict_passthrough

    def test_get_all_paginated_takes_params_and_filter(self):
        sig = inspect.signature(BaseRepository.get_all_paginated)
        params = sig.parameters
        assert params["pagination_params"].annotation is Params
        assert "entity_filter" in params
        assert "options" in params

    def test_delete_takes_uuid(self):
        sig = inspect.signature(BaseRepository.delete)
        assert sig.parameters["entity_id"].annotation is uuid.UUID

    def test_bound_to_base_model(self):
        """The TypeVar T is bound to the declarative Base."""
        from typing import Generic, get_origin

        generic_base = next(
            b for b in BaseRepository.__orig_bases__ if get_origin(b) is Generic
        )
        bound = generic_base.__args__[0].__bound__
        assert bound is Base
