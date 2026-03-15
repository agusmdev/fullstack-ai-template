import threading
from contextvars import ContextVar

from pydantic import BaseModel

# Local ContextVar for request_id — no default so req_or_thread_id falls back
# to thread ID when called outside an HTTP request context (e.g., CLI, tests).
_request_id_ctx: ContextVar[str] = ContextVar("request_id")


def set_request_id(request_id: str) -> None:
    """Set the request ID for the current context."""
    _request_id_ctx.set(request_id)


def req_or_thread_id() -> str:
    """Get the request_id from context, falling back to thread_id if not set."""
    try:
        return _request_id_ctx.get()
    except LookupError:
        return str(threading.get_ident())


class RequestContext(BaseModel):
    user_id: str = "No user id"
    email: str = "No email"


# ContextVar-based storage: automatically scoped to each async Task (HTTP request).
# No explicit cleanup needed for web requests; clear_request_context() is kept for
# tests and non-HTTP contexts (CLI, background tasks) where the ContextVar persists.
_request_context_ctx: ContextVar[RequestContext | None] = ContextVar(
    "request_context", default=None
)


def get_request_context() -> RequestContext:
    ctx = _request_context_ctx.get()
    if ctx is None:
        ctx = RequestContext()
        _request_context_ctx.set(ctx)
    return ctx


def register_request_context(context: RequestContext) -> RequestContext:
    existing = _request_context_ctx.get()
    if existing is not None:
        return existing
    _request_context_ctx.set(context)
    return context


def clear_request_context() -> None:
    """Reset request context.

    Needed for tests and non-HTTP contexts (CLI, background tasks) where the
    ContextVar is not automatically scoped to a single async Task.
    """
    _request_context_ctx.set(None)
