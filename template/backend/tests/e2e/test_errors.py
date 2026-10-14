"""The error contract: every error is a status code plus JSON ``{detail, error_code}``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from tests.e2e.helpers import (
    DEFAULT_PASSWORD,
    EXPIRED,
    NUL,
    assert_error,
    deactivate_user,
    drop_server_connections,
    login,
    unique_email,
)
from tests.e2e.stack import FRONTEND_URL

if TYPE_CHECKING:
    from collections.abc import Callable

    import httpx

    from tests.e2e.helpers import RegisteredUser
    from tests.e2e.stack import Database

# Fixed, so test ids are the same in every process (pytest-xdist needs that).
SOME_ID = "00000000-0000-4000-8000-000000000000"

# Every route that needs a valid session: (method, path, JSON body).
PROTECTED_ROUTES: list[tuple[str, str, dict[str, Any] | None]] = [
    ("GET", "/users/me", None),
    ("PATCH", "/users/me", {"display_name": "x"}),
    ("DELETE", "/users/me", None),
    ("POST", "/auth/logout/all", None),
    ("POST", "/auth/email/verify", None),
    ("GET", "/items", None),
    ("POST", "/items", {"name": "x"}),
    ("GET", f"/items/{SOME_ID}", None),
    ("PATCH", f"/items/{SOME_ID}", {"name": "x"}),
    ("DELETE", f"/items/{SOME_ID}", None),
    ("GET", "/items/by-sku/SKU-1", None),
]


def test_unknown_path_is_404(api: httpx.Client) -> None:
    assert_error(api.get("/no-such-path"), 404, "http_error", "Not Found")


def test_wrong_method_is_405(api: httpx.Client) -> None:
    assert_error(api.delete("/health"), 405, "http_error", "Method Not Allowed")


def test_validation_error_lists_each_invalid_field(api: httpx.Client) -> None:
    response = api.post("/auth/register", json={"email": "not-an-email"})

    body = assert_error(response, 422, "validation_error")
    invalid_fields = {issue["loc"][-1] for issue in body["detail"]}
    assert invalid_fields == {"email", "raw_password"}
    assert all(issue["msg"] for issue in body["detail"])


def test_malformed_json_body_is_422(api: httpx.Client) -> None:
    response = api.post(
        "/auth/login",
        content=b"{not json",
        headers={"content-type": "application/json"},
    )

    body = assert_error(response, 422, "validation_error")
    assert body["detail"][0]["type"] == "json_invalid"


@pytest.mark.parametrize(("method", "path", "body"), PROTECTED_ROUTES)
def test_protected_route_without_credentials_is_403(
    api: httpx.Client, method: str, path: str, body: dict[str, Any] | None
) -> None:
    response = api.request(method, path, json=body)

    assert_error(response, 403, "http_error", "Not authenticated")


@pytest.mark.parametrize(("method", "path", "body"), PROTECTED_ROUTES)
def test_protected_route_with_unknown_session_is_401(
    make_client: Callable[..., httpx.Client],
    method: str,
    path: str,
    body: dict[str, Any] | None,
) -> None:
    token = "s_this-session-does-not-exist"
    response = make_client(token).request(method, path, json=body)

    assert_error(response, 401, "invalid_session", "Invalid session")
    # The error never echoes the bearer token back.
    assert token not in response.text


def test_logout_without_credentials_is_403(api: httpx.Client) -> None:
    # Logout accepts an unknown session (see test_auth), but not a missing one.
    assert_error(api.post("/auth/logout"), 403, "http_error", "Not authenticated")


def test_malformed_authorization_header_is_403(api: httpx.Client) -> None:
    response = api.get("/users/me", headers={"Authorization": "Basic dXNlcjpwdw=="})

    assert_error(response, 403, "http_error", "Invalid authentication credentials")


def test_expired_session_is_401_session_expired(
    register_user: Callable[..., RegisteredUser], db: Database
) -> None:
    user = register_user()
    db.execute(
        "UPDATE session SET expires_at = %s WHERE id = %s", (EXPIRED, user.session_id)
    )

    assert_error(
        user.client.get("/users/me"), 401, "session_expired", "Session expired"
    )


def test_session_of_deactivated_user_is_401_inactive_user(
    register_user: Callable[..., RegisteredUser], db: Database
) -> None:
    user = register_user()
    deactivate_user(db, user.id)

    response = user.client.get("/items")

    assert_error(response, 401, "inactive_user", "User is not allowed to login")


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("GET", "/no-such-path", None),
        ("GET", "/users/me", None),
        ("POST", "/auth/login", {}),
    ],
    ids=["404", "403", "422"],
)
def test_error_responses_carry_cors_headers(
    api: httpx.Client, method: str, path: str, body: dict[str, Any] | None
) -> None:
    # Without them, the browser hides the error body from the frontend.
    response = api.request(method, path, json=body, headers={"Origin": FRONTEND_URL})

    assert response.status_code >= 400
    assert response.headers["access-control-allow-origin"] == FRONTEND_URL


def test_unknown_session_401_carries_cors_headers(
    make_client: Callable[..., httpx.Client],
) -> None:
    client = make_client("s_unknown")

    response = client.get("/users/me", headers={"Origin": FRONTEND_URL})

    assert_error(response, 401, "invalid_session")
    assert response.headers["access-control-allow-origin"] == FRONTEND_URL


# Every input that reaches a text column or a text comparison in Postgres:
# (method, path, JSON body). Postgres text cannot store a NUL character.
NUL_INPUTS: list[tuple[str, str, dict[str, Any] | None]] = [
    ("POST", "/items", {"name": f"a{NUL}b"}),
    ("PATCH", "/users/me", {"display_name": f"a{NUL}b"}),
    ("GET", "/items/by-sku/%00", None),
    ("GET", "/items?search=%00", None),
    ("GET", "/items?name__ilike=%00", None),
    ("POST", "/auth/login", {"email": f"a{NUL}@example.com", "password": "x"}),
    ("POST", "/auth/password/confirm", {"token": NUL, "new_password": "long-enough"}),
    ("POST", "/auth/email/verify/confirm", {"token": NUL}),
]


@pytest.mark.parametrize(("method", "path", "body"), NUL_INPUTS)
def test_nul_character_is_rejected_with_422(
    auth_client: httpx.Client, method: str, path: str, body: dict[str, Any] | None
) -> None:
    response = auth_client.request(method, path, json=body)

    assert_error(
        response, 422, "validation_error", "Text must not contain NUL characters"
    )
    # Nothing was stored, and the connection stays usable.
    assert auth_client.get("/items").json()["total"] == 0
    assert auth_client.get("/users/me").json()["display_name"] == "E2E User"


def test_register_with_a_nul_character_creates_no_account(api: httpx.Client) -> None:
    email = unique_email()

    response = api.post(
        "/auth/register",
        json={"email": email, "raw_password": DEFAULT_PASSWORD, "display_name": NUL},
    )

    assert_error(
        response, 422, "validation_error", "Text must not contain NUL characters"
    )
    assert_error(login(api, email, DEFAULT_PASSWORD), 401, "authentication_error")


def test_unhandled_error_is_a_json_500_the_frontend_can_read(
    register_user: Callable[..., RegisteredUser], db: Database
) -> None:
    user = register_user()
    with drop_server_connections(db, user.client):
        response = user.client.get("/users/me", headers={"Origin": FRONTEND_URL})

    assert_error(response, 500, "internal_server_error", "Internal Server Error")
    assert response.headers["access-control-allow-origin"] == FRONTEND_URL
    # The server recovers, and keeps the connection open: the next request
    # goes over the same TCP connection (uvicorn closes it after a crash).
    follow_up = user.client.get("/users/me")
    assert follow_up.status_code == 200
    stream = follow_up.extensions["network_stream"]
    assert stream is response.extensions["network_stream"]
