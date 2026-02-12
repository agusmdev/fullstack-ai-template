"""Wide events logging system.

This module implements the wide events (canonical log lines) pattern:
- One comprehensive, structured JSON log event per request
- High cardinality fields (user_id, request_id, session_id)
- High dimensionality (many fields per event)
- Business context from handlers

Usage:
    # In main.py
    from app.core.logging import configure_logging
    from app.core.logging.middleware import WideEventMiddleware

    configure_logging()
    app.add_middleware(WideEventMiddleware)

    # In handlers
    from app.core.logging import log_entity, log_action, log_custom

    @router.post("/items")
    async def create_item(item: ItemCreate):
        log_action("create")
        result = await service.create(item)
        log_entity("item", result.id)
        return result
"""

from app.core.logging.config import configure_logging, get_logger
from app.core.logging.context import (
    WideEventContext,
    clear_wide_event_context,
    get_wide_event_context,
    set_wide_event_context,
)
from app.core.logging.helpers import (
    log_action,
    log_custom,
    log_entities,
    log_entity,
    log_user,
)

__all__ = [
    # Configuration
    "configure_logging",
    "get_logger",
    # Context
    "WideEventContext",
    "get_wide_event_context",
    "set_wide_event_context",
    "clear_wide_event_context",
    # Helpers
    "log_action",
    "log_custom",
    "log_entity",
    "log_entities",
    "log_user",
]
