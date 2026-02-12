import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.context import _request_id_ctx


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and set request_id in context."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Generate request_id
        request_id = str(uuid.uuid4())

        # Set in context
        _request_id_ctx.set(request_id)

        # Process request
        response = await call_next(request)

        return response
