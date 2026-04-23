"""Helper functions for adding business context to wide events."""

from typing import Any
from uuid import UUID

from app.core.logging.context import add_entity_to_context, get_wide_event_context


def log_entity(entity_type: str, entity_id: str | UUID) -> None:
    """Add a single entity to the current wide event."""
    add_entity_to_context(entity_type, entity_id)


def log_entities(entity_type: str, entity_ids: list[str | UUID]) -> None:
    """Add multiple entities of the same type to the current wide event."""
    for entity_id in entity_ids:
        add_entity_to_context(entity_type, entity_id)


def log_action(action: str) -> None:
    """Set the business action on the current wide event."""
    ctx = get_wide_event_context()
    if ctx is not None:
        ctx.action = action


def log_custom(**kwargs: Any) -> None:
    """Add arbitrary key-value context to the current wide event."""
    ctx = get_wide_event_context()
    if ctx is not None:
        ctx.custom.update(kwargs)


def log_user(user_id: str | UUID, email: str | None = None) -> None:
    """Set authenticated user context on the current wide event."""
    ctx = get_wide_event_context()
    if ctx is not None:
        ctx.user_id = str(user_id)
        if email:
            ctx.email = email
