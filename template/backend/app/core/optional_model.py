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


def _transform_annotation_to_partial(
    annotation: Any, cache: dict[type[BaseModel], type[BaseModel]]
) -> Any:
    """Transform type annotation to use partial BaseModel versions."""
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
                # Extract from Optional if we wrapped it
                if get_origin(transformed) is Union and type(None) in get_args(
                    transformed
                ):
                    non_none_args = [
                        a for a in get_args(transformed) if a is not type(None)
                    ]
                    if len(non_none_args) == 1:
                        new_args.append(non_none_args[0])
                    else:
                        new_args.append(transformed)
                else:
                    new_args.append(transformed)
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
            transformed_arg = _transform_annotation_to_partial(args[0], cache)
            # Extract from Optional if we wrapped it
            if get_origin(transformed_arg) is Union and type(None) in get_args(
                transformed_arg
            ):
                non_none_args = [
                    a for a in get_args(transformed_arg) if a is not type(None)
                ]
                if len(non_none_args) == 1:
                    return Optional[list[non_none_args[0]]]  # type: ignore[valid-type]
            return Optional[list[transformed_arg]]
        return Optional[annotation]
    elif hasattr(annotation, "__origin__") and args:
        # Handle other generic types
        new_args = []
        for arg in args:
            transformed_arg = _transform_annotation_to_partial(arg, cache)
            # Extract from Optional if we wrapped it
            if get_origin(transformed_arg) is Union and type(None) in get_args(
                transformed_arg
            ):
                non_none_args = [
                    a for a in get_args(transformed_arg) if a is not type(None)
                ]
                if len(non_none_args) == 1:
                    new_args.append(non_none_args[0])
                else:
                    new_args.append(transformed_arg)
            else:
                new_args.append(transformed_arg)
        # Reconstruct the generic type
        try:
            return Optional[origin[tuple(new_args)]]
        except (TypeError, AttributeError):
            return Optional[annotation]

    return Optional[annotation]
