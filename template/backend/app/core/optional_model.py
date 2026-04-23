# ruff: noqa: UP045 (This file uses Optional[...] for dynamic type manipulation)
from copy import deepcopy
from typing import (
    Any,
    Optional,
    Union,
    get_args,
    get_origin,
)

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


def recursive_partial_model(
    model: type[BaseModel],
    _cache: dict[type[BaseModel], type[BaseModel]] | None = None,
) -> type[BaseModel]:
    """
    Create a partial model where all fields (including nested BaseModel fields) are optional.

    This function recursively processes nested BaseModel fields, making them optional while
    preserving the structure and validation rules. It handles complex types like List[BaseModel],
    Union types, and prevents infinite recursion through caching.

    Args:
        model: The BaseModel class to make partial
        _cache: Internal cache to prevent infinite recursion (do not pass manually)

    Returns:
        A new BaseModel class with all fields optional, including nested models

    Example:
        >>> class Address(BaseModel):
        ...     street: str
        ...     city: str
        ...
        >>> class User(BaseModel):
        ...     name: str
        ...     age: int
        ...     address: Address
        ...     addresses: List[Address]
        ...
        >>> PartialUser = recursive_partial_model(User)
        >>> user = PartialUser()  # All fields are optional
        >>> user = PartialUser(name="John")  # Partial instantiation works
    """
    # Initialize cache on first call
    if _cache is None:
        _cache = {}

    # Return cached result if already processed
    if model in _cache:
        return _cache[model]

    # Create the partial model name
    partial_name = f"Partial{model.__name__}"

    # Create placeholder in cache to prevent infinite recursion
    _cache[model] = None  # type: ignore

    # First, recursively process all nested BaseModel types
    nested_models = set()
    for _field_name, field_info in model.model_fields.items():
        nested_models.update(_extract_nested_basemodels(field_info.annotation))

    # Process nested models that aren't already cached and aren't self-references
    for nested_model in nested_models:
        if nested_model not in _cache and nested_model is not model:
            recursive_partial_model(nested_model, _cache)

    def make_field_optional_recursive(field: FieldInfo) -> tuple[Any, FieldInfo]:
        """Make a field optional and transform nested BaseModels to use partial versions."""
        new_field = deepcopy(field)
        new_field.default = None

        # Transform the annotation to use partial models
        new_annotation = _transform_annotation_to_partial(field.annotation, _cache)
        new_field.annotation = new_annotation

        return new_annotation, new_field

    # Process all fields
    partial_fields = {}
    for field_name, field_info in model.model_fields.items():
        partial_fields[field_name] = make_field_optional_recursive(field_info)

    # Create the partial model
    partial_model_class: type[BaseModel] = create_model(
        partial_name,
        __base__=model,
        __module__=model.__module__,
        **partial_fields,
    )

    # Update cache with actual model
    _cache[model] = partial_model_class

    return partial_model_class


def _extract_nested_basemodels(annotation: Any) -> list[type[BaseModel]]:
    """Extract BaseModel types from type annotations, handling forward references."""
    basemodel_types: list[type[BaseModel]] = []

    # Handle string annotations (forward references)
    if isinstance(annotation, str):
        # For forward references, we can't process them at this stage
        return basemodel_types

    # Direct BaseModel check
    if (
        isinstance(annotation, type)
        and issubclass(annotation, BaseModel)
        and annotation is not BaseModel
    ):
        basemodel_types.append(annotation)
        return basemodel_types

    # Handle Optional[T] (which is Union[T, None])
    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is Union:
        # Process each type in the Union
        for arg in args:
            if arg is not type(None):  # Skip None type
                basemodel_types.extend(_extract_nested_basemodels(arg))
    elif origin is list:
        # Handle List[T]
        if args:
            basemodel_types.extend(_extract_nested_basemodels(args[0]))
    elif hasattr(annotation, "__origin__") and args:
        # Handle other generic types
        for arg in args:
            basemodel_types.extend(_extract_nested_basemodels(arg))

    return basemodel_types


def _unwrap_if_optional(annotation: Any) -> Any:
    """Return the inner type if annotation is Optional[T], otherwise return annotation unchanged."""
    if get_origin(annotation) is Union and type(None) in get_args(annotation):
        non_none = [a for a in get_args(annotation) if a is not type(None)]
        if len(non_none) == 1:
            return non_none[0]
    return annotation


def _transform_annotation_to_partial(
    annotation: Any, cache: dict[type[BaseModel], type[BaseModel]]
) -> Any:
    """Recursively rewrite a type annotation so embedded BaseModels become their partial versions.

    Strategy:
    - **Direct BaseModel**: replace with ``Optional[cache[model]]`` if the model has been
      processed (is in cache). The ``Optional`` wrapper ensures the field can be omitted.
    - **Union[T, None] (Optional[T])**: process the inner type; re-wrap the result as Union
      without double-nesting ``None``.
    - **List[T]**: transform the element type; return ``Optional[list[T']]``.
    - **Other generic types** (e.g. ``Dict[K, V]``): transform each argument and attempt to
      reconstruct the generic; fall back to ``Optional[annotation]`` on failure.
    - **Scalar types / forward references**: return ``Optional[annotation]`` unchanged.

    The caller (``recursive_partial_model``) always wraps the final annotation in
    ``Optional``; this function handles intermediate nesting so Union/list containers
    do not end up with double ``None`` entries.
    """
    # Handle string annotations (forward references)
    if isinstance(annotation, str):
        return Optional[annotation]

    # Direct BaseModel replacement
    if (
        isinstance(annotation, type)
        and issubclass(annotation, BaseModel)
        and annotation in cache
        and cache[annotation] is not None
    ):
        return Optional[cache[annotation]]

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is Union:
        # Transform BaseModels in Union types
        new_args = []
        for arg in args:
            if arg is type(None):
                new_args.append(arg)
            elif (
                isinstance(arg, type)
                and issubclass(arg, BaseModel)
                and arg in cache
                and cache[arg] is not None
            ):
                new_args.append(cache[arg])
            else:
                transformed = _transform_annotation_to_partial(arg, cache)
                new_args.append(_unwrap_if_optional(transformed))
        return (
            Optional[tuple(new_args)]
            if len(new_args) > 1
            else Optional[new_args[0]]
            if new_args
            else Optional[annotation]
        )
    elif origin is list:
        # Transform BaseModels in List types
        if args:
            transformed_arg = _unwrap_if_optional(_transform_annotation_to_partial(args[0], cache))
            return Optional[list[transformed_arg]]  # type: ignore[valid-type]
        return Optional[annotation]
    elif hasattr(annotation, "__origin__") and args:
        # Handle other generic types
        new_args = [
            _unwrap_if_optional(_transform_annotation_to_partial(arg, cache))
            for arg in args
        ]
        # Reconstruct the generic type
        try:
            return Optional[origin[tuple(new_args)]]
        except (TypeError, AttributeError):
            return Optional[annotation]

    return Optional[annotation]
