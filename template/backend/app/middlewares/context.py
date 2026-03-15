import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.context import set_request_id
from app.core.logging.context import get_wide_event_context


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and set request_id in context."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Reuse the ID already set by WideEventMiddleware (outermost) if present,
        # so that both the wide event log and the request context share one canonical ID.
        wide_ctx = get_wide_event_context()
        request_id = wide_ctx.request_id if wide_ctx is not None else str(uuid.uuid4())
        set_request_id(request_id)

        # Process request
        response = await call_next(request)

        return response
