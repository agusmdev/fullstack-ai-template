import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.context import set_request_id


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and set request_id in context."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid.uuid4())
        set_request_id(request_id)

        # Process request
        response = await call_next(request)

        return response
