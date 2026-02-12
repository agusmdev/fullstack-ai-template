"""Tests for RequestContextMiddleware."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.middlewares.context import RequestContextMiddleware


class TestRequestContextMiddleware:
    """Tests for RequestContextMiddleware."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        app = MagicMock()
        return RequestContextMiddleware(app)

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = MagicMock()
        return request

    @pytest.fixture
    def mock_call_next(self):
        """Create mock call_next function."""
        response = MagicMock()
        return AsyncMock(return_value=response)

    async def test_dispatch_generates_request_id(self, middleware, mock_request, mock_call_next):
        """Test that dispatch generates a request_id."""
        from app.context import _request_id_ctx

        response = await middleware.dispatch(mock_request, mock_call_next)

        # Request ID should have been set
        request_id = _request_id_ctx.get()
        assert request_id is not None
        assert isinstance(request_id, str)

    async def test_dispatch_calls_next(self, middleware, mock_request, mock_call_next):
        """Test that dispatch calls the next middleware/handler."""
        await middleware.dispatch(mock_request, mock_call_next)

        mock_call_next.assert_called_once_with(mock_request)

    async def test_dispatch_returns_response(self, middleware, mock_request, mock_call_next):
        """Test that dispatch returns the response."""
        expected_response = MagicMock()
        mock_call_next.return_value = expected_response

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result is expected_response

    async def test_request_id_is_uuid_format(self, middleware, mock_request, mock_call_next):
        """Test that request_id is in UUID format."""
        import uuid

        from app.context import _request_id_ctx

        await middleware.dispatch(mock_request, mock_call_next)

        request_id = _request_id_ctx.get()
        # Should be parseable as UUID
        parsed = uuid.UUID(request_id)
        assert str(parsed) == request_id
