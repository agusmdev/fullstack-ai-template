"""Wide event context for structured logging."""

from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.core.logging.sanitizer import sanitize_dict

# ContextVar storage (async-safe)
_wide_event_ctx: ContextVar["WideEventContext | None"] = ContextVar(
    "wide_event", default=None
)


@dataclass
class WideEventContext:
    """Context for wide events (canonical log lines).

    One instance per request, accumulates all relevant context
    and is emitted as a single log event at request completion.
    """

    # Request identification
    request_id: str
    trace_id: str | None = None

    # User context (set by auth)
    user_id: str | None = None
    email: str | None = None
    session_id: str | None = None

    # Request metadata (set by middleware)
    method: str = ""
    path: str = ""
    path_template: str | None = None
    client_ip: str = "unknown"
    query_string: str | None = None

    # Response (finalized at completion)
    status_code: int = 0
    duration_ms: float = 0.0

    # Business context (set by handlers)
    entity_type: str | None = None
    entity_id: str | None = None
    entity_ids: list[str] = field(default_factory=list)
    action: str | None = None
    # Free-form business context added via log_custom(). Keys are arbitrary string
    # labels; values must be JSON-serializable. Common keys: "resource", "reason",
    # "provider", "source". Sanitized before emission (see sanitize_dict).
    custom: dict[str, Any] = field(default_factory=dict)

    # Error context
    error: bool = False
    error_type: str | None = None
    error_message: str | None = None

    # Timing
    _start_time: float = field(default=0.0, repr=False)

    def set_error(self, error_type: str, error_message: str) -> None:
        """Set error context."""
        self.error = True
        self.error_type = error_type
        self.error_message = error_message

    def finalize(self, status_code: int, duration_ms: float) -> None:
        """Finalize the context with response data."""
        self.status_code = status_code
        self.duration_ms = duration_ms

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging, omitting None values and internal fields."""
        data: dict[str, Any] = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "request_id": self.request_id,
            "method": self.method,
            "path": self.path,
            "status_code": self.status_code,
            "duration_ms": round(self.duration_ms, 2),
            "client_ip": self.client_ip,
        }

        # Optional fields - only include if set
        if self.trace_id:
            data["trace_id"] = self.trace_id
        if self.user_id:
            data["user_id"] = self.user_id
        if self.email:
            data["email"] = self.email
        if self.session_id:
            data["session_id"] = self.session_id
        if self.path_template and self.path_template != self.path:
            data["path_template"] = self.path_template
        if self.query_string:
            data["query_string"] = self.query_string
        if self.entity_type:
            data["entity_type"] = self.entity_type
        if self.entity_id:
            data["entity_id"] = self.entity_id
        if self.entity_ids:
            data["entity_ids"] = self.entity_ids
        if self.action:
            data["action"] = self.action
        if self.custom:
            data["custom"] = sanitize_dict(self.custom)
        if self.error:
            data["error"] = True
            if self.error_type:
                data["error_type"] = self.error_type
            if self.error_message:
                data["error_message"] = self.error_message

        return data


def get_wide_event_context() -> WideEventContext | None:
    """Get the current wide event context."""
    return _wide_event_ctx.get()


def set_wide_event_context(ctx: WideEventContext) -> None:
    """Set the wide event context for the current request."""
    _wide_event_ctx.set(ctx)


def clear_wide_event_context() -> None:
    """Clear the wide event context after request completion."""
    _wide_event_ctx.set(None)


def add_entity_to_context(entity_type: str, entity_id: str | UUID) -> None:
    """Add entity context to the current wide event."""
    ctx = get_wide_event_context()
    if ctx is None:
        return

    entity_id_str = str(entity_id)
    ctx.entity_type = entity_type

    # If single entity, set entity_id; if multiple, use entity_ids
    if ctx.entity_id is None and not ctx.entity_ids:
        ctx.entity_id = entity_id_str
    else:
        # Move single to list if needed
        if ctx.entity_id and ctx.entity_id not in ctx.entity_ids:
            ctx.entity_ids.append(ctx.entity_id)
            ctx.entity_id = None
        if entity_id_str not in ctx.entity_ids:
            ctx.entity_ids.append(entity_id_str)
