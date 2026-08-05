# ruff: noqa: UP045 (This file uses Optional[...] for dynamic type manipulation)
from copy import deepcopy
from typing import Any, Optional

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

# https://stackoverflow.com/questions/67699451/make-every-field-as-optional-with-pydantic
# https://github.com/pydantic/pydantic/issues/1673#issuecomment-1841811370


def partial_model(model: type[BaseModel]) -> type[BaseModel]:
    """Class decorator that makes all fields optional with a default of None.

    Used on update schemas so PATCH endpoints accept partial payloads — only the
    fields present in the request body are updated, others remain unchanged.

    Args:
        model: A Pydantic BaseModel class whose fields should all become optional.

    Returns:
        A new model class named ``Partial<OriginalName>`` where every field is
        ``Optional[original_type]`` with ``default=None``.

    Example::

        @partial_model
        class ItemUpdate(ItemBase):
            pass
        # ItemUpdate(name="new name")  # only name; description is None
    """

    def make_field_optional(
        field: FieldInfo, default: Any = None
    ) -> tuple[Any, FieldInfo]:
        new = deepcopy(field)
        new.default = default
        new.annotation = Optional[field.annotation]
        return new.annotation, new

    return create_model(  # type: ignore[no-any-return, call-overload]
        f"Partial{model.__name__}",
        __base__=model,
        __module__=model.__module__,
        **{
            field_name: make_field_optional(field_info)
            for field_name, field_info in model.model_fields.items()
        },
    )
