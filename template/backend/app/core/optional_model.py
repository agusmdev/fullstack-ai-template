from copy import deepcopy
from typing import Any

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

# https://stackoverflow.com/questions/67699451/make-every-field-as-optional-with-pydantic
# https://github.com/pydantic/pydantic/issues/1673#issuecomment-1841811370


def partial_model(model: type[BaseModel]) -> type[BaseModel]:
    """Class decorator that makes every field omittable, for PATCH payloads.

    Only the fields present in the request body are updated (callers dump with
    ``exclude_unset=True``); omitted fields stay unchanged.

    A field keeps its original type, so ``null`` is accepted only when the
    original type allows ``None`` (for example ``description: str | None``).
    Sending ``null`` for a required column (for example ``name: str``) is a 422
    validation error, not a NOT NULL violation in the database.

    Args:
        model: A Pydantic BaseModel class whose fields should become omittable.

    Returns:
        A new model class named ``Partial<OriginalName>`` where every field has
        ``default=None``. The default is not validated, so an omitted field
        never fails validation and is not part of ``exclude_unset`` dumps.

    Example::

        @partial_model
        class ItemUpdate(ItemBase):
            pass
        # ItemUpdate(name="new name")  # only name is set
        # ItemUpdate(name=None)        # ValidationError: name is not nullable
    """

    def make_field_omittable(field: FieldInfo) -> tuple[Any, FieldInfo]:
        new = deepcopy(field)
        new.default = None
        return field.annotation, new

    return create_model(  # type: ignore[no-any-return, call-overload]
        f"Partial{model.__name__}",
        __base__=model,
        __module__=model.__module__,
        **{
            field_name: make_field_omittable(field_info)
            for field_name, field_info in model.model_fields.items()
        },
    )
