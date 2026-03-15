from typing import Any

from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy import Select, or_
from sqlalchemy.orm import Query


def _backward_compatible_value_for_like_and_ilike(value: str) -> str:
    """Add % if not in value to be backward compatible.

    Args:
        value (str): The value to filter.

    Returns:
        Either the unmodified value if a percent sign is present, the value wrapped in % otherwise to preserve
        current behavior.
    """
    if "%" not in value:
        # warn(
        #     "You must pass the % character explicitly to use the like and ilike operators.",
        #     DeprecationWarning,
        #     stacklevel=2,
        # )
        value = f"%{value}%"
    return value


_orm_operator_transformer: dict[
    str, Any
] = {  # Type is complex due to lambda return types
    "neq": lambda value: ("__ne__", value),
    "gt": lambda value: ("__gt__", value),
    "gte": lambda value: ("__ge__", value),
    "in": lambda value: ("in_", value),
    "isnull": lambda value: ("is_", None) if value is True else ("is_not", None),
    "lt": lambda value: ("__lt__", value),
    "lte": lambda value: ("__le__", value),
    "like": lambda value: (
        "like",
        _backward_compatible_value_for_like_and_ilike(value),
    ),
    "ilike": lambda value: (
        "ilike",
        _backward_compatible_value_for_like_and_ilike(value),
    ),
    # XXX(arthurio): Mysql excludes None values when using `in` or `not in` filters.
    "not": lambda value: ("is_not", value),
    "not_in": lambda value: ("not_in", value),
}


class JoinFilter(Filter):
    def filter(self, query: Query[Any] | Select[Any]) -> Query[Any] | Select[Any]:
        for field_name, value in self.filtering_fields:
            field_value = getattr(self, field_name)
            if isinstance(field_value, Filter):
                field_value_dump = field_value.model_dump(
                    exclude_unset=True, exclude_none=True
                )
                if field_value_dump and any(field_value_dump.values()):
                    joins = getattr(self.Constants, "joins", {})
                    if joins and field_name in joins:
                        join = joins[field_name]
                        join["target"] = join.pop("target", field_value.Constants.model)
                        query = query.join(**join)

                    query = field_value.filter(query)
            else:
                if "__" in field_name:
                    field_name, operator = field_name.split("__")
                    operator, value = _orm_operator_transformer[operator](value)
                else:
                    operator = "__eq__"

                if field_name == self.Constants.search_field_name and hasattr(
                    self.Constants, "search_model_fields"
                ):
                    search_filters = [
                        getattr(self.Constants.model, field).ilike(f"%{value}%")
                        for field in self.Constants.search_model_fields
                    ]
                    query = query.filter(or_(*search_filters))
                else:
                    model_field = getattr(self.Constants.model, field_name)
                    query = query.filter(getattr(model_field, operator)(value))

        return query
