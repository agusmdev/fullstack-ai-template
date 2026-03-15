from __future__ import annotations

from collections import deque
from collections.abc import Callable
from types import UnionType
from typing import (
    TYPE_CHECKING,
    Any,
    Union,
    get_args,
    get_origin,
)

from loguru import logger
from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pydantic.fields import FieldInfo

SELECT_STRATEGY_KEY = "_select_strategy"

type JsonDict = dict[str, Any]
type JsonSchemaExtra = JsonDict | Callable[[JsonDict], None]


def pydantic_field_name(name: str, field: FieldInfo) -> str:
    if field.alias:
        return field.alias
    return name


def should_ignore_field(field: FieldInfo) -> bool:
    if field.json_schema_extra:
        extra = field.json_schema_extra
        if isinstance(extra, dict):
            return extra.get(SELECT_STRATEGY_KEY) == "lazy"  # type: ignore[invalid-argument-type]
    return False


def pydantic_model_fields(
    model: type[BaseModel], prefix: str = "", *, max_depth: int = 100
) -> Iterator[str]:
    """
    Returns flat names for all fields in a Pydantic model.

    Args:
        model: The Pydantic model to extract fields from.
        prefix: Prefix to add to field names (used for nested models).
        max_depth: Maximum recursion depth to prevent infinite loops with recursive models.

    Yields:
        Flat field names in dot notation (e.g., "user.profile.name").
    """

    def _pydantic_model(ann: Any) -> type[BaseModel] | None:
        """Extract a Pydantic model from a type annotation.

        Only checks container types that commonly contain BaseModel:
        Union, Optional, list, set, and tuple.
        """
        origin = get_origin(ann)

        # Check for PEP 604 union (A | B) and typing.Union
        if origin in (Union, list, set, tuple) or isinstance(ann, UnionType):
            args_to_check = get_args(ann) if origin else (ann,)
            for arg in args_to_check:
                if pydantic_model := _pydantic_model(arg):
                    return pydantic_model

        if isinstance(ann, type) and issubclass(ann, BaseModel):
            return ann

        return None

    # Use a set to track visited models and prevent infinite recursion
    visited: set[tuple[str, type[BaseModel]]] = set()
    queue = deque([(prefix, model, 0)])  # (prefix, model, depth)

    while queue:
        prefix, current_model, depth = queue.popleft()

        # Prevent infinite recursion with depth limit
        if depth >= max_depth:
            logger.warning(
                f"Maximum recursion depth ({max_depth}) reached for model {current_model.__name__}. "
                "Some fields may be omitted."
            )
            continue

        # Skip models we've already processed at this prefix (cycle detection)
        visit_key = (prefix, current_model)
        if visit_key in visited:
            continue
        visited.add(visit_key)

        for name, field in current_model.model_fields.items():
            if should_ignore_field(field):
                continue

            ann = field.annotation
            field_name = pydantic_field_name(name, field)

            if nested_model := _pydantic_model(ann):
                queue.append((f"{prefix}{field_name}.", nested_model, depth + 1))
            else:
                yield f"{prefix}{field_name}"


class PydanticGraph:
    """
    Graph that represents the field structure and relationships
    of a Pydantic model.
    """

    def __init__(self, columns: list[str], relationships: dict[str, PydanticGraph]):
        self.columns: list[str] = columns
        self.relationships: dict[str, PydanticGraph] = relationships

    def add_node(self, node: str) -> None:
        if "." in node:
            relationship, sub_node = node.split(".", 1)

            if relationship not in self.relationships:
                self.relationships[relationship] = PydanticGraph([], {})
            self.relationships[relationship].add_node(sub_node)
        else:
            self.columns.append(node)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PydanticGraph):
            return False

        return (
            self.columns == other.columns and self.relationships == other.relationships
        )

    @classmethod
    def from_model(cls, fields: type[BaseModel]) -> PydanticGraph:
        model_fields = pydantic_model_fields(fields)

        graph = cls([], {})
        for field in model_fields:
            graph.add_node(field)
        return graph
