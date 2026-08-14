"""Tests for WideEventMiddleware.

The dispatch/emit behavior is verified through a real FastAPI request pipeline
(TestClient → middleware → route → response) so the assertions describe the
actual emitted wide-event payload (method, path, status, client IP, error
context, log level) rather than confirming only that mocks were called.
The pure helpers (_get_client_ip, _get_route_template) are tested with real
starlette Request objects built from ASGI scopes.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.core.logging import middleware as mw_module
from app.core.logging.context import WideEventContext
from app.core.logging.middleware import WideEventMiddleware


def _scope(path="/", method="GET", headers=None, client=("127.0.0.1", 60000)):
    """Build a minimal ASGI scope for a real starlette Request."""
    raw_headers = []
    for key, value in (headers or {}).items():
        raw_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))
    return {
        "type": "http",
        "method": method,
        "path": path,
        "raw_path": path.encode("latin-1"),
        "query_string": b"",
        "headers": raw_headers,
        "client": client,
        "scheme": "http",
        "server": ("test", 80),
        "app": None,
    }


@pytest.fixture
def captured_logger(monkeypatch):
    """Patch the module-level logger and record every emitted wide event."""
    events: list[dict] = []
    levels: list[tuple[str, str]] = []

    bound = MagicMock()

    def _log(level, msg):
        levels.append((level, msg))

    bound.log.side_effect = _log

    mock_logger = MagicMock()

    def _bind(**kwargs):
        events.append(kwargs)
        return bound

    mock_logger.bind.side_effect = _bind

    monkeypatch.setattr(mw_module, "logger", mock_logger)
    return events, levels


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(WideEventMiddleware)
    return app


class TestDispatchHTTPFlow:
    """End-to-end dispatch behavior through a real request pipeline."""

    def test_successful_request_emits_info_payload(self, captured_logger):
        events, levels = captured_logger
        app = _build_app()

        @app.get("/ok")
        def ok():
            return {"x": 1}

        with TestClient(app) as client:
            response = client.get(
                "/ok",
                headers={"X-Forwarded-For": "9.9.9.9, 1.1.1.1"},
                params={"q": "1"},
            )

        assert response.status_code == 200
        assert levels == [("INFO", "request_completed")]
        assert len(events) == 1
        payload = events[0]
        assert payload["method"] == "GET"
        assert payload["path"] == "/ok"
        assert payload["status_code"] == 200
        assert payload["client_ip"] == "9.9.9.9"  # first IP of X-Forwarded-For
        assert payload["query_string"] == "q=1"
        assert payload["duration_ms"] >= 0.0
        assert "request_id" in payload and payload["request_id"]

    def test_4xx_response_logs_at_warning(self, captured_logger):
        events, levels = captured_logger
        app = _build_app()

        with TestClient(app) as client:
            response = client.get("/missing")

        assert response.status_code == 404
        assert levels == [("WARNING", "request_completed")]
        assert events[0]["status_code"] == 404

    def test_5xx_response_logs_at_error_with_error_context(self, captured_logger):
        events, levels = captured_logger
        app = _build_app()

        @app.get("/boom")
        def boom():
            raise RuntimeError("kaboom")

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/boom")

        assert response.status_code == 500
        assert levels == [("ERROR", "request_completed")]
        payload = events[0]
        assert payload["status_code"] == 500
        assert payload["error"] is True
        assert payload["error_type"] == "RuntimeError"
        assert payload["error_message"] == "kaboom"

    def test_trace_id_propagated_from_header(self, captured_logger):
        events, _ = captured_logger
        app = _build_app()

        @app.get("/ok")
        def ok():
            return {"x": 1}

        with TestClient(app) as client:
            client.get("/ok", headers={"X-Trace-Id": "trace-abc"})

        assert events[0]["trace_id"] == "trace-abc"


class TestGetClientIp:
    """_get_client_ip header precedence — verified with real Request objects."""

    def test_extracts_first_ip_from_x_forwarded_for(self):
        mw = WideEventMiddleware(MagicMock())
        request = Request(_scope(headers={"X-Forwarded-For": "10.0.0.1, 192.168.1.1"}))

        assert mw._get_client_ip(request) == "10.0.0.1"

    def test_strips_whitespace_from_forwarded_for(self):
        mw = WideEventMiddleware(MagicMock())
        request = Request(
            _scope(headers={"X-Forwarded-For": "  10.0.0.1  , 192.168.1.1"})
        )

        assert mw._get_client_ip(request) == "10.0.0.1"

    def test_extracts_from_x_real_ip(self):
        mw = WideEventMiddleware(MagicMock())
        request = Request(_scope(headers={"X-Real-IP": "172.16.0.1"}))

        assert mw._get_client_ip(request) == "172.16.0.1"

    def test_falls_back_to_client_host(self):
        mw = WideEventMiddleware(MagicMock())
        request = Request(_scope(client=("203.0.113.5", 1234)))

        assert mw._get_client_ip(request) == "203.0.113.5"

    def test_returns_unknown_when_no_client(self):
        mw = WideEventMiddleware(MagicMock())
        request = Request(_scope(client=None))

        assert mw._get_client_ip(request) == "unknown"


class TestGetRouteTemplate:
    """_get_route_template matches a mounted route to its path template."""

    def test_returns_matched_route_path(self):
        app = _build_app()

        @app.get("/items/{item_id}")
        def get_item(item_id: str):
            return {}

        mw = WideEventMiddleware(app)
        # A real Request needs the app's routes available — build scope referencing the app.
        request = Request(
            {**_scope(path="/items/42"), "app": app, "router": app.router}
        )

        assert mw._get_route_template(request) == "/items/{item_id}"

    def test_returns_none_when_no_app(self):
        mw = WideEventMiddleware(MagicMock())
        request = Request(_scope())

        assert mw._get_route_template(request) is None


class TestEmitWideEventLevelMapping:
    """_emit_wide_event selects the log level from status/error — direct checks."""

    @pytest.fixture
    def captured_logger_for_emit(self, captured_logger):
        return captured_logger

    def test_info_for_2xx(self, captured_logger_for_emit):
        events, levels = captured_logger_for_emit
        mw = WideEventMiddleware(MagicMock())

        ctx = WideEventContext(request_id="req-1")
        ctx.status_code = 201
        mw._emit_wide_event(ctx)

        assert levels == [("INFO", "request_completed")]

    def test_warning_for_4xx(self, captured_logger_for_emit):
        _, levels = captured_logger_for_emit
        mw = WideEventMiddleware(MagicMock())

        ctx = WideEventContext(request_id="req-1")
        ctx.status_code = 404
        mw._emit_wide_event(ctx)

        assert levels == [("WARNING", "request_completed")]

    def test_error_for_5xx(self, captured_logger_for_emit):
        _, levels = captured_logger_for_emit
        mw = WideEventMiddleware(MagicMock())

        ctx = WideEventContext(request_id="req-1")
        ctx.status_code = 500
        mw._emit_wide_event(ctx)

        assert levels == [("ERROR", "request_completed")]

    def test_error_when_error_flag_set_even_on_2xx(self, captured_logger_for_emit):
        _, levels = captured_logger_for_emit
        mw = WideEventMiddleware(MagicMock())

        ctx = WideEventContext(request_id="req-1")
        ctx.status_code = 200
        ctx.error = True
        mw._emit_wide_event(ctx)

        assert levels == [("ERROR", "request_completed")]
