"""Tests for ExternalApiService."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from app.services.exceptions import ExternalApiException
from app.services.external_api_service import ExternalApiService


class TestExternalApiServiceInit:
    """Tests for ExternalApiService initialization."""

    def test_basic_init(self):
        """Test basic initialization."""
        service = ExternalApiService(base_url="https://api.example.com")
        assert service.base_url == "https://api.example.com"
        assert service.headers == {}
        assert service.return_json is True

    def test_init_with_headers(self):
        """Test initialization with headers."""
        headers = {"Authorization": "Bearer token123"}
        service = ExternalApiService(base_url="https://api.example.com", headers=headers)
        assert service.headers == headers

    def test_init_with_return_json_false(self):
        """Test initialization with return_json=False."""
        service = ExternalApiService(base_url="https://api.example.com", return_json=False)
        assert service.return_json is False


class TestExternalApiServiceMethods:
    """Tests for ExternalApiService HTTP methods."""

    @pytest.fixture
    def service(self):
        return ExternalApiService(base_url="https://api.example.com")

    @pytest.fixture
    def mock_response(self):
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"success": True, "data": "test"}
        return response

    @patch("app.services.external_api_service.requests.request")
    def test_get_success(self, mock_request, service, mock_response):
        """Test successful GET request."""
        mock_request.return_value = mock_response

        result = service.get("/endpoint")

        mock_request.assert_called_once_with(
            method="get",
            url="https://api.example.com/endpoint",
            headers={},
        )
        assert result == {"success": True, "data": "test"}

    @patch("app.services.external_api_service.requests.request")
    def test_post_success(self, mock_request, service, mock_response):
        """Test successful POST request."""
        mock_request.return_value = mock_response

        result = service.post("/endpoint", json={"key": "value"})

        mock_request.assert_called_once_with(
            method="post",
            url="https://api.example.com/endpoint",
            headers={},
            json={"key": "value"},
        )
        assert result == {"success": True, "data": "test"}

    @patch("app.services.external_api_service.requests.request")
    def test_put_success(self, mock_request, service, mock_response):
        """Test successful PUT request."""
        mock_request.return_value = mock_response

        result = service.put("/endpoint", json={"key": "value"})

        mock_request.assert_called_once_with(
            method="put",
            url="https://api.example.com/endpoint",
            headers={},
            json={"key": "value"},
        )
        assert result["success"] is True

    @patch("app.services.external_api_service.requests.request")
    def test_patch_success(self, mock_request, service, mock_response):
        """Test successful PATCH request."""
        mock_request.return_value = mock_response

        result = service.patch("/endpoint", json={"key": "value"})

        mock_request.assert_called_once_with(
            method="patch",
            url="https://api.example.com/endpoint",
            headers={},
            json={"key": "value"},
        )
        assert result["success"] is True

    @patch("app.services.external_api_service.requests.request")
    def test_delete_success(self, mock_request, service, mock_response):
        """Test successful DELETE request."""
        mock_request.return_value = mock_response

        result = service.delete("/endpoint")

        mock_request.assert_called_once_with(
            method="delete",
            url="https://api.example.com/endpoint",
            headers={},
        )
        assert result["success"] is True


class TestExternalApiServiceHeaders:
    """Tests for ExternalApiService header handling."""

    @patch("app.services.external_api_service.requests.request")
    def test_uses_instance_headers(self, mock_request):
        """Test that instance headers are used."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        service = ExternalApiService(
            base_url="https://api.example.com",
            headers={"Authorization": "Bearer token123"},
        )
        service.get("/endpoint")

        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["headers"] == {"Authorization": "Bearer token123"}

    @patch("app.services.external_api_service.requests.request")
    def test_override_headers(self, mock_request):
        """Test that headers can be overridden per request."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        service = ExternalApiService(
            base_url="https://api.example.com",
            headers={"Authorization": "Bearer default"},
        )
        service.get("/endpoint", headers={"Authorization": "Bearer override"})

        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["headers"] == {"Authorization": "Bearer override"}


class TestExternalApiServiceReturnJson:
    """Tests for ExternalApiService return_json behavior."""

    @patch("app.services.external_api_service.requests.request")
    def test_return_json_true(self, mock_request):
        """Test return_json=True returns parsed JSON."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "value"}
        mock_request.return_value = mock_response

        service = ExternalApiService(base_url="https://api.example.com", return_json=True)
        result = service.get("/endpoint")

        mock_response.json.assert_called_once()
        assert result == {"key": "value"}

    @patch("app.services.external_api_service.requests.request")
    def test_return_json_false(self, mock_request):
        """Test return_json=False returns response object."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "value"}
        mock_request.return_value = mock_response

        service = ExternalApiService(base_url="https://api.example.com", return_json=False)
        result = service.get("/endpoint")

        mock_response.json.assert_not_called()
        assert result == mock_response


class TestExternalApiServiceErrorHandling:
    """Tests for ExternalApiService error handling."""

    @pytest.fixture
    def service(self):
        return ExternalApiService(base_url="https://api.example.com")

    @patch("app.services.external_api_service.requests.request")
    def test_http_error_raises_exception(self, mock_request, service):
        """Test HTTP error raises ExternalApiException."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_request.return_value = mock_response

        with pytest.raises(ExternalApiException) as exc_info:
            service.get("/not-found")

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Not Found"

    @patch("app.services.external_api_service.requests.request")
    def test_server_error_raises_exception(self, mock_request, service):
        """Test server error raises ExternalApiException."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_request.return_value = mock_response

        with pytest.raises(ExternalApiException) as exc_info:
            service.get("/error")

        assert exc_info.value.status_code == 500

    @patch("app.services.external_api_service.requests.request")
    def test_error_preserves_original_exception(self, mock_request, service):
        """Test that original exception is preserved as __cause__."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        original_error = requests.exceptions.HTTPError()
        mock_response.raise_for_status.side_effect = original_error
        mock_request.return_value = mock_response

        with pytest.raises(ExternalApiException) as exc_info:
            service.get("/bad-request")

        assert exc_info.value.__cause__ is original_error


class TestExternalApiServiceUrlConstruction:
    """Tests for ExternalApiService URL construction."""

    @patch("app.services.external_api_service.requests.request")
    def test_url_concatenation(self, mock_request):
        """Test URL is correctly constructed."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        service = ExternalApiService(base_url="https://api.example.com")
        service.get("/users/123")

        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["url"] == "https://api.example.com/users/123"

    @patch("app.services.external_api_service.requests.request")
    def test_base_url_without_trailing_slash(self, mock_request):
        """Test base URL without trailing slash."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        service = ExternalApiService(base_url="https://api.example.com")
        service.get("/endpoint")

        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["url"] == "https://api.example.com/endpoint"
