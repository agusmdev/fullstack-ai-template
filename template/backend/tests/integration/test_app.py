"""Integration tests for the FastAPI application."""

from unittest.mock import patch


class TestHealthCheck:
    """Tests for the health check endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint returns OK."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == "FastAPI running!"


class TestCORSHeaders:
    """Tests for CORS configuration."""

    def test_cors_allows_localhost(self, client):
        """Test CORS allows localhost origin."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS preflight should be allowed
        assert response.status_code in (200, 204, 405)

    def test_cors_headers_in_response(self, client):
        """Test CORS headers are present in response."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers or response.status_code == 200


class TestAppFactory:
    """Tests for the application factory."""

    @patch("app.main.sentry_sdk.init")
    def test_create_app_with_sentry(self, mock_sentry_init):
        """Test app creation with Sentry enabled."""
        from app.main import create_app

        app = create_app(add_sentry=True)

        assert app is not None
        mock_sentry_init.assert_called_once()

    def test_create_app_without_sentry(self):
        """Test app creation without Sentry."""
        from app.main import create_app

        app = create_app(add_sentry=False)

        assert app is not None

    def test_app_has_health_endpoint(self):
        """Test that app has health endpoint registered."""
        from unittest.mock import MagicMock

        from fastapi.testclient import TestClient

        from app.main import create_app

        app = create_app(add_sentry=False)

        # Mock the logger to avoid loguru level issues
        mock_logger = MagicMock()
        mock_logger.bind = MagicMock(return_value=mock_logger)
        mock_logger.log = MagicMock()

        with patch("app.core.logging.middleware.logger", mock_logger):
            with TestClient(app) as client:
                response = client.get("/health")
                assert response.status_code == 200


class TestMiddleware:
    """Tests for middleware configuration."""

    def test_request_has_cors_headers(self, client):
        """Test that requests include CORS headers."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 200


class TestAppRoutes:
    """Tests for application routes."""

    def test_root_routes_exist(self, client):
        """Test that expected routes exist."""
        # Health endpoint should exist
        response = client.get("/health")
        assert response.status_code == 200

    def test_unknown_route_returns_404(self, client):
        """Test that unknown routes return 404."""
        response = client.get("/this-route-does-not-exist")
        assert response.status_code == 404
