"""Helper functions for adding business context to wide events.

These functions provide a simple API for handlers to enrich log events
with business-specific context without directly manipulating the context object.
"""

from typing import Any
from uuid import UUID

from app.core.logging.context import add_entity_to_context, get_wide_event_context


def log_entity(entity_type: str, entity_id: str | UUID) -> None:
    """Add entity context to the wide event.

    Args:
        entity_type: Type of entity (e.g., "item", "user", "order")
        entity_id: Unique identifier for the entity

    Example:
        log_entity("item", item.id)
    """
    add_entity_to_context(entity_type, entity_id)


def log_entities(entity_type: str, entity_ids: list[str | UUID]) -> None:
    """Add multiple entities of the same type to the wide event.

    Args:
        entity_type: Type of entities
        entity_ids: List of entity identifiers

    Example:
        log_entities("item", [item1.id, item2.id])
    """
    for entity_id in entity_ids:
        add_entity_to_context(entity_type, entity_id)


def log_action(action: str) -> None:
    """Add business action context to the wide event.

    Args:
        action: The action being performed (e.g., "create", "update", "delete", "list")

    Example:
        log_action("create")
    """
    ctx = get_wide_event_context()
    if ctx is not None:
        ctx.action = action


def log_custom(**kwargs: Any) -> None:
    """Add arbitrary business context to the wide event.

    Args:
        **kwargs: Key-value pairs to add to the custom context

    Example:
        log_custom(order_total=99.99, items_count=3)
    """
    ctx = get_wide_event_context()
    if ctx is not None:
        ctx.custom.update(kwargs)


def log_user(user_id: str | UUID, email: str | None = None) -> None:
    """Set user context in the wide event.

    This should be called by authentication logic to populate user context.

    Args:
        user_id: The authenticated user's ID
        email: The authenticated user's email (optional)

    Example:
        log_user(session.user.id, session.user.email)
    """
    ctx = get_wide_event_context()
    if ctx is not None:
        ctx.user_id = str(user_id)
        if email:
            ctx.email = email
