"""Register, log in, log out: sessions issued and revoked by the real auth endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from tests.e2e.helpers import (
    DEFAULT_PASSWORD,
    assert_error,
    create_passwordless_user,
    deactivate_user,
    login,
    unique_email,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    import httpx

    from tests.e2e.helpers import RegisteredUser
    from tests.e2e.stack import Database

ONE_YEAR_S = 365 * 24 * 3600


def test_register_returns_a_session_for_the_new_user(
    api: httpx.Client, make_client: Callable[..., httpx.Client]
) -> None:
    email = unique_email()

    response = api.post(
        "/auth/register",
        json={"email": email, "raw_password": "s3cret-pass", "display_name": "Ada"},
    )

    assert response.status_code == 201
    session = response.json()
    assert set(session) == {"id", "expires_at", "expires_in"}
    assert session["id"].startswith("s_")
    assert ONE_YEAR_S - 60 < session["expires_in"] <= ONE_YEAR_S
    # Timezone-aware, like every timestamp of the API: a naive value would be
    # read as local time by the browser.
    expires_at = datetime.fromisoformat(session["expires_at"])
    assert expires_at.tzinfo is not None
    remaining = (expires_at - datetime.now(UTC)).total_seconds()
    assert abs(remaining - session["expires_in"]) < 60

    me = make_client(session["id"]).get("/users/me")
    assert me.status_code == 200
    assert me.json()["email"] == email
    assert me.json()["display_name"] == "Ada"


def test_register_rejects_an_email_that_is_taken(
    api: httpx.Client, register_user: Callable[..., RegisteredUser]
) -> None:
    user = register_user()

    response = api.post(
        "/auth/register", json={"email": user.email, "raw_password": "other-password"}
    )

    assert_error(response, 400, "duplicate_item", "Duplicate entry found in User")
    # The original account still logs in with its own password.
    assert login(api, user.email, user.password).status_code == 200


def test_register_rejects_an_invalid_email(api: httpx.Client) -> None:
    response = api.post(
        "/auth/register",
        json={"email": "not-an-email", "raw_password": DEFAULT_PASSWORD},
    )

    body = assert_error(response, 422, "validation_error")
    assert [issue["loc"] for issue in body["detail"]] == [["body", "email"]]


@pytest.mark.parametrize("password", ["", "short-7"])
def test_register_rejects_a_password_shorter_than_8(
    api: httpx.Client, password: str
) -> None:
    email = unique_email()

    response = api.post(
        "/auth/register", json={"email": email, "raw_password": password}
    )

    body = assert_error(response, 422, "validation_error")
    assert [issue["loc"] for issue in body["detail"]] == [["body", "raw_password"]]
    assert_error(login(api, email, password), 401, "authentication_error")


def test_email_is_stored_lowercase_and_matches_in_any_case(
    api: httpx.Client, make_client: Callable[..., httpx.Client]
) -> None:
    email = unique_email()
    mixed_case = email.replace("user", "User").replace("example", "EXAMPLE")

    registered = api.post(
        "/auth/register", json={"email": mixed_case, "raw_password": DEFAULT_PASSWORD}
    )

    assert registered.status_code == 201
    me = make_client(registered.json()["id"]).get("/users/me").json()
    assert me["email"] == email
    assert login(api, email.upper(), DEFAULT_PASSWORD).status_code == 200
    # The same address in another case is the same account.
    duplicate = api.post(
        "/auth/register", json={"email": email, "raw_password": DEFAULT_PASSWORD}
    )
    assert_error(duplicate, 400, "duplicate_item")


def test_login_issues_a_new_session_each_time(
    api: httpx.Client,
    register_user: Callable[..., RegisteredUser],
    make_client: Callable[..., httpx.Client],
) -> None:
    user = register_user()

    first = login(api, user.email, user.password)
    second = login(api, user.email, user.password)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] != second.json()["id"]
    for session in (first.json(), second.json()):
        assert make_client(session["id"]).get("/users/me").json()["id"] == user.id


def test_login_with_a_wrong_password_is_401(
    api: httpx.Client, register_user: Callable[..., RegisteredUser]
) -> None:
    user = register_user()

    response = login(api, user.email, "wrong-password")

    assert_error(response, 401, "invalid_password", "Invalid password")


def test_login_with_an_unknown_email_is_401(api: httpx.Client) -> None:
    response = login(api, unique_email(), DEFAULT_PASSWORD)

    assert_error(
        response,
        401,
        "authentication_error",
        "User does not exist or is not allowed to login",
    )


def test_account_without_password_cannot_log_in_with_one(
    api: httpx.Client, db: Database
) -> None:
    email = unique_email("oauth")
    create_passwordless_user(db, email)

    response = login(api, email, DEFAULT_PASSWORD)

    assert_error(response, 401, "invalid_password", "Invalid password")


def test_login_requires_email_and_password(api: httpx.Client) -> None:
    body = assert_error(api.post("/auth/login", json={}), 422, "validation_error")

    assert {issue["loc"][-1] for issue in body["detail"]} == {"email", "password"}


def test_deactivated_user_cannot_log_in(
    api: httpx.Client, register_user: Callable[..., RegisteredUser], db: Database
) -> None:
    user = register_user()
    deactivate_user(db, user.id)

    response = login(api, user.email, user.password)

    assert_error(
        response,
        401,
        "authentication_error",
        "User does not exist or is not allowed to login",
    )


def test_logout_ends_only_the_current_session(
    api: httpx.Client,
    register_user: Callable[..., RegisteredUser],
    make_client: Callable[..., httpx.Client],
) -> None:
    user = register_user()
    other_device = make_client(login(api, user.email, user.password).json()["id"])

    response = user.client.post("/auth/logout")

    assert response.status_code == 200
    assert response.json() == {
        "status": "logged_out",
        "message": "Successfully logged out",
    }
    assert_error(user.client.get("/users/me"), 401, "invalid_session")
    assert other_device.get("/users/me").status_code == 200


def test_logout_with_an_unknown_session_still_succeeds(
    make_client: Callable[..., httpx.Client],
) -> None:
    # Logout must work for a session that is already gone or expired.
    response = make_client("s_unknown-session").post("/auth/logout")

    assert response.status_code == 200
    assert response.json()["status"] == "logged_out"


def test_logout_all_ends_every_session_of_the_user(
    api: httpx.Client,
    register_user: Callable[..., RegisteredUser],
    make_client: Callable[..., httpx.Client],
) -> None:
    user = register_user()
    other_user = register_user()
    other_device = make_client(login(api, user.email, user.password).json()["id"])

    response = user.client.post("/auth/logout/all")

    assert response.status_code == 200
    assert response.json() == {
        "status": "logged_out",
        "message": "Successfully logged out from all devices",
    }
    assert_error(user.client.get("/users/me"), 401, "invalid_session")
    assert_error(other_device.get("/users/me"), 401, "invalid_session")
    # Other users keep their sessions, and the user can log in again.
    assert other_user.client.get("/users/me").status_code == 200
    assert login(api, user.email, user.password).status_code == 200
