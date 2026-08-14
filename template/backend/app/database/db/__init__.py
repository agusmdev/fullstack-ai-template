"""Pydantic-driven SQLAlchemy eager-load optimizer (template showcase subsystem).

This package builds SQLAlchemy ``load_only`` / ``joinedload`` options by reflecting
on a Pydantic response model, so repositories fetch exactly the columns and
relationships the schema needs (no N+1, no over-fetching).

Entry points
------------
* ``select_from_pydantic(model, schema)`` -> list of ``Load`` options.
* Reached in production via ``app.repositories.query_builder.QueryBuilder`` and
  ``app.repositories.sql_repository.SQLAlchemyRepository`` whenever a
  ``response_model`` is supplied to ``get()`` / ``get_by_field()`` (e.g. session
  validation in ``app.user.auth``), and optionally via
  ``QueryOptions.response_model`` on list/paginated queries.

Scope note
-----------
This is a self-contained, opt-in optimization layer. It is NOT used by the
default ``get_all`` / ``get_all_paginated`` paths unless a caller explicitly
passes a ``response_model`` (today only the auth ``get_by_field`` path opts in;
``QueryOptions.response_model`` is not set by any production caller). Treat this
package as an isolated showcase: changes here should not affect callers that do
not pass ``response_model``.
"""

from .code_generator import QueryOptimizerError as QueryOptimizerError
from .pydantic_fields import PydanticGraph as PydanticGraph
from .statement_generator import StatementGenerator as StatementGenerator
from .statement_generator import select_from_pydantic as select_from_pydantic
