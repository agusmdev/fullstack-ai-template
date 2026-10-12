"""Base class for the list filters of the API (fastapi-filter on SQLAlchemy)."""

from typing import Any

from fastapi_filter.contrib.sqlalchemy.filter import Filter
from pydantic import ValidationInfo, field_validator
from sqlalchemy import inspect


class ModelFilter(Filter):
    """A fastapi-filter ``Filter`` that sorts only by the model's columns.

    fastapi-filter accepts any ``?order_by=`` name that is an attribute of the
    model. Names such as ``metadata`` or ``__table__`` are attributes but not
    columns: the query build then fails and the API sends a 500. This class
    rejects them, so the API sends a 422 validation error.
    """

    @field_validator("*", mode="after", check_fields=False)
    @classmethod
    def order_by_names_columns(cls, value: Any, info: ValidationInfo) -> Any:
        """Accept only ``[-|+]<column>`` names in the ordering field."""
        if info.field_name != cls.Constants.ordering_field_name or not value:
            return value
        columns = set(inspect(cls.Constants.model).column_attrs.keys())
        for name in value:
            field_name = name.removeprefix("-").removeprefix("+")
            if field_name not in columns:
                raise ValueError(f"{field_name} is not a valid ordering field.")
        return value
