"""Health check, API docs and CORS: the parts every client depends on."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.e2e.stack import FRONTEND_URL

if TYPE_CHECKING:
    import httpx


def test_health_reports_the_api_is_running(api: httpx.Client) -> None:
    response = api.get("/health")

    assert response.status_code == 200
    assert response.json() == "FastAPI running!"


def test_openapi_schema_describes_the_api(api: httpx.Client) -> None:
    response = api.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert {
        "/auth/register",
        "/auth/login",
        "/users/me",
        "/items",
        "/items/{item_id}",
    } <= paths.keys()
    # Regression: the list filters must be query parameters, not a GET body.
    list_items = paths["/items"]["get"]
    assert "requestBody" not in list_items
    query_params = {p["name"] for p in list_items["parameters"] if p["in"] == "query"}
    assert {"page", "size", "order_by", "name__ilike", "search"} <= query_params


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/docs/oauth2-redirect"])
def test_api_docs_pages_are_served(api: httpx.Client, path: str) -> None:
    response = api.get(path)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_cors_preflight_allows_the_frontend_origin(api: httpx.Client) -> None:
    response = api.options(
        "/items",
        headers={
            "Origin": FRONTEND_URL,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == FRONTEND_URL
    assert response.headers["access-control-allow-credentials"] == "true"
    allowed_headers = response.headers["access-control-allow-headers"].lower()
    assert "authorization" in allowed_headers


def test_cors_preflight_rejects_an_unknown_origin(api: httpx.Client) -> None:
    response = api.options(
        "/items",
        headers={
            "Origin": "http://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_cors_headers_are_on_regular_responses(api: httpx.Client) -> None:
    response = api.get("/health", headers={"Origin": FRONTEND_URL})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == FRONTEND_URL
