"""Tests for ExternalApiService."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.integrations.http_client import ExternalApiException, ExternalApiService


def _make_response(status_code=200, json_data=None, text=""):
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_data if json_data is not None else {}
    response.text = text
    response.raise_for_status = MagicMock()
    return response


def _make_http_error(status_code, text):
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.text = text
    request = MagicMock(spec=httpx.Request)
    return httpx.HTTPStatusError("error", request=request, response=response)


def _patch_client(mock_response):
    """Context manager that patches httpx.AsyncClient to return mock_response."""
    mock_client = AsyncMock()
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client_cls = MagicMock()
    mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)
    return patch("app.integrations.http_client.httpx.AsyncClient", mock_client_cls), mock_client


class TestExternalApiServiceInit:
    """Tests for ExternalApiService initialization."""

    def test_basic_init(self):
        service = ExternalApiService(base_url="https://api.example.com")
        assert service.base_url == "https://api.example.com"
        assert service.headers == {}
        assert service.return_json is True

    def test_init_with_headers(self):
        headers = {"Authorization": "Bearer token123"}
        service = ExternalApiService(base_url="https://api.example.com", headers=headers)
        assert service.headers == headers

    def test_init_with_return_json_false(self):
        service = ExternalApiService(base_url="https://api.example.com", return_json=False)
        assert service.return_json is False


class TestExternalApiServiceMethods:
    """Tests for ExternalApiService HTTP methods."""

    @pytest.fixture
    def service(self):
        return ExternalApiService(base_url="https://api.example.com")

    @pytest.mark.asyncio
    async def test_get_success(self, service):
        mock_response = _make_response(json_data={"success": True, "data": "test"})
        patcher, mock_client = _patch_client(mock_response)
        with patcher:
            result = await service.get("/endpoint")

        mock_client.request.assert_called_once_with(
            method="GET",
            url="https://api.example.com/endpoint",
            headers={},
        )
        assert result == {"success": True, "data": "test"}

    @pytest.mark.asyncio
    async def test_post_success(self, service):
        mock_response = _make_response(json_data={"success": True, "data": "test"})
        patcher, mock_client = _patch_client(mock_response)
        with patcher:
            result = await service.post("/endpoint", json={"key": "value"})

        mock_client.request.assert_called_once_with(
            method="POST",
            url="https://api.example.com/endpoint",
            headers={},
            json={"key": "value"},
        )
        assert result == {"success": True, "data": "test"}

    @pytest.mark.asyncio
    async def test_put_success(self, service):
        mock_response = _make_response(json_data={"success": True})
        patcher, mock_client = _patch_client(mock_response)
        with patcher:
            result = await service.put("/endpoint", json={"key": "value"})

        mock_client.request.assert_called_once_with(
            method="PUT",
            url="https://api.example.com/endpoint",
            headers={},
            json={"key": "value"},
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_patch_success(self, service):
        mock_response = _make_response(json_data={"success": True})
        patcher, mock_client = _patch_client(mock_response)
        with patcher:
            result = await service.patch("/endpoint", json={"key": "value"})

        mock_client.request.assert_called_once_with(
            method="PATCH",
            url="https://api.example.com/endpoint",
            headers={},
            json={"key": "value"},
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_success(self, service):
        mock_response = _make_response(json_data={"success": True})
        patcher, mock_client = _patch_client(mock_response)
        with patcher:
            result = await service.delete("/endpoint")

        mock_client.request.assert_called_once_with(
            method="DELETE",
            url="https://api.example.com/endpoint",
            headers={},
        )
        assert result["success"] is True


class TestExternalApiServiceHeaders:
    """Tests for ExternalApiService header handling."""

    @pytest.mark.asyncio
    async def test_uses_instance_headers(self):
        mock_response = _make_response(json_data={})
        patcher, mock_client = _patch_client(mock_response)
        service = ExternalApiService(
            base_url="https://api.example.com",
            headers={"Authorization": "Bearer token123"},
        )
        with patcher:
            await service.get("/endpoint")

        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["headers"] == {"Authorization": "Bearer token123"}

    @pytest.mark.asyncio
    async def test_override_headers(self):
        mock_response = _make_response(json_data={})
        patcher, mock_client = _patch_client(mock_response)
        service = ExternalApiService(
            base_url="https://api.example.com",
            headers={"Authorization": "Bearer default"},
        )
        with patcher:
            await service.get("/endpoint", headers={"Authorization": "Bearer override"})

        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["headers"] == {"Authorization": "Bearer override"}


class TestExternalApiServiceReturnJson:
    """Tests for ExternalApiService return_json behavior."""

    @pytest.mark.asyncio
    async def test_return_json_true(self):
        mock_response = _make_response(json_data={"key": "value"})
        patcher, _ = _patch_client(mock_response)
        service = ExternalApiService(base_url="https://api.example.com", return_json=True)
        with patcher:
            result = await service.get("/endpoint")

        mock_response.json.assert_called_once()
        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_return_json_false(self):
        mock_response = _make_response(json_data={"key": "value"})
        patcher, _ = _patch_client(mock_response)
        service = ExternalApiService(base_url="https://api.example.com", return_json=False)
        with patcher:
            result = await service.get("/endpoint")

        mock_response.json.assert_not_called()
        assert result is mock_response


class TestExternalApiServiceErrorHandling:
    """Tests for ExternalApiService error handling."""

    @pytest.fixture
    def service(self):
        return ExternalApiService(base_url="https://api.example.com")

    @pytest.mark.asyncio
    async def test_http_error_raises_exception(self, service):
        error = _make_http_error(404, "Not Found")
        mock_response = _make_response()
        mock_response.raise_for_status.side_effect = error
        patcher, _ = _patch_client(mock_response)
        with patcher:
            with pytest.raises(ExternalApiException) as exc_info:
                await service.get("/not-found")

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Not Found"

    @pytest.mark.asyncio
    async def test_server_error_raises_exception(self, service):
        error = _make_http_error(500, "Internal Server Error")
        mock_response = _make_response()
        mock_response.raise_for_status.side_effect = error
        patcher, _ = _patch_client(mock_response)
        with patcher:
            with pytest.raises(ExternalApiException) as exc_info:
                await service.get("/error")

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_error_preserves_original_exception(self, service):
        original_error = _make_http_error(400, "Bad Request")
        mock_response = _make_response()
        mock_response.raise_for_status.side_effect = original_error
        patcher, _ = _patch_client(mock_response)
        with patcher:
            with pytest.raises(ExternalApiException) as exc_info:
                await service.get("/bad-request")

        assert exc_info.value.__cause__ is original_error


class TestExternalApiServiceUrlConstruction:
    """Tests for ExternalApiService URL construction."""

    @pytest.mark.asyncio
    async def test_url_concatenation(self):
        mock_response = _make_response(json_data={})
        patcher, mock_client = _patch_client(mock_response)
        service = ExternalApiService(base_url="https://api.example.com")
        with patcher:
            await service.get("/users/123")

        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["url"] == "https://api.example.com/users/123"

    @pytest.mark.asyncio
    async def test_base_url_without_trailing_slash(self):
        mock_response = _make_response(json_data={})
        patcher, mock_client = _patch_client(mock_response)
        service = ExternalApiService(base_url="https://api.example.com")
        with patcher:
            await service.get("/endpoint")

        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["url"] == "https://api.example.com/endpoint"
