"""Tests for WideEventMiddleware."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.routing import Match

from app.core.logging.middleware import WideEventMiddleware


class TestWideEventMiddleware:
    """Tests for WideEventMiddleware."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        app = MagicMock()
        return WideEventMiddleware(app)

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = MagicMock()
        request.method = "GET"
        request.url.path = "/api/items"
        request.url.query = ""
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.app = None
        return request

    @pytest.fixture
    def mock_call_next(self):
        """Create mock call_next function."""
        response = MagicMock()
        response.status_code = 200
        return AsyncMock(return_value=response)


class TestWideEventMiddlewareDispatch:
    """Tests for WideEventMiddleware.dispatch method."""

    @pytest.fixture
    def middleware(self):
        app = MagicMock()
        return WideEventMiddleware(app)

    @pytest.fixture
    def mock_request(self):
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/users"
        request.url.query = ""
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "192.168.1.1"
        request.app = None
        return request

    @patch("app.core.logging.middleware.logger")
    async def test_dispatch_returns_response(self, mock_logger, middleware, mock_request):
        """Test dispatch returns the response."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_call_next = AsyncMock(return_value=mock_response)

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result is mock_response

    @patch("app.core.logging.middleware.logger")
    async def test_dispatch_calls_next(self, mock_logger, middleware, mock_request):
        """Test dispatch calls call_next."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_call_next = AsyncMock(return_value=mock_response)

        await middleware.dispatch(mock_request, mock_call_next)

        mock_call_next.assert_called_once_with(mock_request)


class TestWideEventMiddlewareGetClientIp:
    """Tests for _get_client_ip method."""

    @pytest.fixture
    def middleware(self):
        app = MagicMock()
        return WideEventMiddleware(app)

    def test_extracts_from_x_forwarded_for(self, middleware):
        """Test extracts IP from X-Forwarded-For header."""
        request = MagicMock()
        request.headers = {"x-forwarded-for": "10.0.0.1, 192.168.1.1"}

        result = middleware._get_client_ip(request)

        assert result == "10.0.0.1"

    def test_extracts_from_x_real_ip(self, middleware):
        """Test extracts IP from X-Real-IP header."""
        request = MagicMock()
        request.headers = {"x-real-ip": "172.16.0.1"}

        result = middleware._get_client_ip(request)

        assert result == "172.16.0.1"

    def test_uses_client_host_as_fallback(self, middleware):
        """Test uses client.host as fallback."""
        request = MagicMock()
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        result = middleware._get_client_ip(request)

        assert result == "127.0.0.1"

    def test_returns_unknown_when_no_client(self, middleware):
        """Test returns 'unknown' when no client info."""
        request = MagicMock()
        request.headers = {}
        request.client = None

        result = middleware._get_client_ip(request)

        assert result == "unknown"

    def test_strips_whitespace_from_forwarded_for(self, middleware):
        """Test strips whitespace from X-Forwarded-For."""
        request = MagicMock()
        request.headers = {"x-forwarded-for": "  10.0.0.1  , 192.168.1.1"}

        result = middleware._get_client_ip(request)

        assert result == "10.0.0.1"


class TestWideEventMiddlewareGetRouteTemplate:
    """Tests for _get_route_template method."""

    @pytest.fixture
    def middleware(self):
        app = MagicMock()
        return WideEventMiddleware(app)

    def test_returns_none_when_no_app(self, middleware):
        """Test returns None when no app."""
        request = MagicMock()
        request.app = None

        result = middleware._get_route_template(request)

        assert result is None

    def test_returns_route_path_on_match(self, middleware):
        """Test returns route path when match found."""
        mock_route = MagicMock()
        mock_route.matches.return_value = (Match.FULL, {})
        mock_route.path = "/items/{item_id}"

        request = MagicMock()
        request.app.routes = [mock_route]
        request.scope = {}

        result = middleware._get_route_template(request)

        assert result == "/items/{item_id}"

    def test_returns_none_on_no_match(self, middleware):
        """Test returns None when no route matches."""
        mock_route = MagicMock()
        mock_route.matches.return_value = (Match.NONE, {})

        request = MagicMock()
        request.app.routes = [mock_route]
        request.scope = {}

        result = middleware._get_route_template(request)

        assert result is None


class TestWideEventMiddlewareEmitWideEvent:
    """Tests for _emit_wide_event method."""

    @pytest.fixture
    def middleware(self):
        app = MagicMock()
        return WideEventMiddleware(app)

    @patch("app.core.logging.middleware.logger")
    def test_logs_info_for_2xx(self, mock_logger, middleware):
        """Test logs at info level for 2xx status codes."""
        from app.core.logging.context import WideEventContext

        ctx = WideEventContext(request_id="req-123")
        ctx.status_code = 200

        middleware._emit_wide_event(ctx)

        mock_logger.bind.assert_called_once()
        mock_logger.bind().log.assert_called_once_with("info", "request_completed")

    @patch("app.core.logging.middleware.logger")
    def test_logs_warning_for_4xx(self, mock_logger, middleware):
        """Test logs at warning level for 4xx status codes."""
        from app.core.logging.context import WideEventContext

        ctx = WideEventContext(request_id="req-123")
        ctx.status_code = 404

        middleware._emit_wide_event(ctx)

        mock_logger.bind.assert_called_once()
        mock_logger.bind().log.assert_called_once_with("warning", "request_completed")

    @patch("app.core.logging.middleware.logger")
    def test_logs_error_for_5xx(self, mock_logger, middleware):
        """Test logs at error level for 5xx status codes."""
        from app.core.logging.context import WideEventContext

        ctx = WideEventContext(request_id="req-123")
        ctx.status_code = 500

        middleware._emit_wide_event(ctx)

        mock_logger.bind.assert_called_once()
        mock_logger.bind().log.assert_called_once_with("error", "request_completed")

    @patch("app.core.logging.middleware.logger")
    def test_logs_error_when_error_flag_set(self, mock_logger, middleware):
        """Test logs at error level when error flag is set."""
        from app.core.logging.context import WideEventContext

        ctx = WideEventContext(request_id="req-123")
        ctx.status_code = 200
        ctx.error = True

        middleware._emit_wide_event(ctx)

        mock_logger.bind().log.assert_called_once_with("error", "request_completed")
