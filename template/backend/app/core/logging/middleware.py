"""Wide event middleware for structured logging."""

import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any, Literal

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match

from app.core.logging.context import (
    WideEventContext,
    clear_wide_event_context,
    set_wide_event_context,
)


class WideEventMiddleware(BaseHTTPMiddleware):
    """Middleware that emits one comprehensive log event per request.

    This implements the wide events (canonical log lines) pattern:
    - One log entry per request at completion
    - High cardinality fields (user_id, request_id, etc.)
    - High dimensionality (many fields per event)
    - Business context from handlers

    Args:
        app: The ASGI application.
        on_request_cleanup: Optional callback invoked after each request to clean up
            request-scoped state (e.g., clearing a request context cache). Injected
            at registration time so core does not depend on app-level modules.
    """

    def __init__(
        self,
        app: Any,
        on_request_cleanup: Callable[[], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(app, **kwargs)
        self._on_request_cleanup = on_request_cleanup or (lambda: None)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Create context for this request
        request_id = str(uuid.uuid4())
        ctx = WideEventContext(request_id=request_id)
        set_wide_event_context(ctx)

        # Populate request metadata
        ctx.method = request.method
        ctx.path = request.url.path
        ctx.client_ip = self._get_client_ip(request)
        ctx.path_template = self._get_route_template(request)
        ctx.trace_id = request.headers.get("x-trace-id") or request.headers.get(
            "x-request-id"
        )

        # Capture query string (without sensitive params)
        if request.url.query:
            ctx.query_string = str(request.url.query)

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
            ctx.finalize(response.status_code, duration_ms)
            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            ctx.set_error(type(exc).__name__, str(exc))
            ctx.finalize(status_code=500, duration_ms=duration_ms)
            raise

        finally:
            self._emit_wide_event(ctx)
            clear_wide_event_context()
            self._on_request_cleanup()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, considering common proxy headers."""
        # Check X-Forwarded-For first (common for load balancers/proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP (original client)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP (nginx)
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        if request.client:
            return request.client.host

        return "unknown"

    def _get_route_template(self, request: Request) -> str | None:
        """Extract the route template (e.g., /items/{item_id}) if available."""
        # Try to match the route to get the path template
        if request.app and hasattr(request.app, "routes"):
            for route in request.app.routes:
                match, _ = route.matches(request.scope)
                if match == Match.FULL:
                    if hasattr(route, "path"):
                        return route.path
        return None

    def _emit_wide_event(self, ctx: WideEventContext) -> None:
        """Emit the wide event log."""
        event_data = ctx.to_dict()

        # Determine log level based on status code
        level: Literal["ERROR", "WARNING", "INFO"]
        if ctx.error or ctx.status_code >= 500:
            level = "ERROR"
        elif ctx.status_code >= 400:
            level = "WARNING"
        else:
            level = "INFO"

        # Log with all context bound
        logger.bind(**event_data).log(level, "request_completed")
