import threading
from contextvars import ContextVar
from uuid import uuid4

from pydantic import BaseModel

# Local ContextVar for request_id (replaces fastapi_injector's _request_id_ctx)
_request_id_ctx: ContextVar[str] = ContextVar("request_id", default=str(uuid4()))


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


_request_context_cache: dict[str, RequestContext] = {}


def get_request_context() -> RequestContext:
    request_id = req_or_thread_id()
    if ctx := _request_context_cache.get(request_id):
        return ctx

    ctx = RequestContext()
    _request_context_cache[request_id] = ctx
    return ctx


def fork_request_context(context: RequestContext) -> RequestContext:
    request_id = req_or_thread_id()
    if ctx := _request_context_cache.get(request_id):
        # If it already exists do nothing
        return ctx

    _request_context_cache[request_id] = context
    return context


def clear_request_context() -> None:
    """Clean up context cache after request completion.

    This prevents unbounded memory growth by removing the context
    entry for the current request when the request is complete.
    """
    request_id = req_or_thread_id()
    _request_context_cache.pop(request_id, None)
