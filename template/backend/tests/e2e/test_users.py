"""The logged-in user's profile: read, update, delete (/users/me)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.e2e.helpers import (
    assert_error,
    create_item,
    email_verification_token,
    login,
    password_reset_token,
    unique_email,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    import httpx

    from tests.e2e.helpers import RegisteredUser
    from tests.e2e.stack import Database


def test_me_returns_the_profile_without_secrets(
    register_user: Callable[..., RegisteredUser],
) -> None:
    user = register_user(display_name="Grace")

    response = user.client.get("/users/me")

    assert response.status_code == 200
    assert response.json() == {
        "id": user.id,
        "email": user.email,
        "display_name": "Grace",
        "email_verified_at": None,
        "is_email_verified": False,
    }


def test_update_changes_only_the_sent_fields(
    register_user: Callable[..., RegisteredUser],
) -> None:
    user = register_user(display_name="Before")

    response = user.client.patch("/users/me", json={"display_name": "After"})

    assert response.status_code == 200
    assert response.json()["display_name"] == "After"
    me = user.client.get("/users/me").json()
    assert me["display_name"] == "After"
    assert me["email"] == user.email


def test_updated_email_is_the_new_login(
    api: httpx.Client, register_user: Callable[..., RegisteredUser]
) -> None:
    user = register_user()
    new_email = unique_email("renamed")

    response = user.client.patch("/users/me", json={"email": new_email})

    assert response.status_code == 200
    assert response.json()["email"] == new_email
    assert login(api, new_email, user.password).status_code == 200
    assert_error(login(api, user.email, user.password), 401, "authentication_error")


def test_updated_email_is_stored_lowercase(
    api: httpx.Client, register_user: Callable[..., RegisteredUser]
) -> None:
    user = register_user()
    new_email = unique_email("renamed")

    response = user.client.patch("/users/me", json={"email": new_email.upper()})

    assert response.status_code == 200
    assert user.client.get("/users/me").json()["email"] == new_email
    assert login(api, new_email, user.password).status_code == 200


def test_update_ignores_protected_fields(
    api: httpx.Client, register_user: Callable[..., RegisteredUser]
) -> None:
    user = register_user(display_name="Before")
    other = register_user()

    response = user.client.patch(
        "/users/me",
        json={
            "display_name": "After",
            "id": other.id,
            "is_active": False,
            "password": "taken-over-password",
            "raw_password": "taken-over-password",
            "email_verified_at": "2020-01-01T00:00:00Z",
        },
    )

    # Only display_name is a profile field; the rest is ignored.
    assert response.status_code == 200
    me = user.client.get("/users/me")  # still active
    assert me.status_code == 200
    assert me.json() == {
        "id": user.id,
        "email": user.email,
        "display_name": "After",
        "email_verified_at": None,
        "is_email_verified": False,
    }
    assert login(api, user.email, user.password).status_code == 200
    assert_error(login(api, user.email, "taken-over-password"), 401, "invalid_password")
    assert other.client.get("/users/me").json()["id"] == other.id


def test_update_rejects_an_email_another_user_has(
    register_user: Callable[..., RegisteredUser],
) -> None:
    user = register_user()
    other = register_user()

    response = user.client.patch("/users/me", json={"email": other.email})

    assert_error(response, 400, "duplicate_item", "Duplicate entry found in User")
    assert user.client.get("/users/me").json()["email"] == user.email


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "not-an-email"},
        # Regression: explicit null on a NOT NULL column was a 500.
        {"email": None},
        {"display_name": None},
    ],
)
def test_update_rejects_invalid_values(
    register_user: Callable[..., RegisteredUser], payload: dict[str, object]
) -> None:
    user = register_user(display_name="Unchanged")

    response = user.client.patch("/users/me", json=payload)

    body = assert_error(response, 422, "validation_error")
    assert body["detail"][0]["loc"] == ["body", *payload]
    me = user.client.get("/users/me").json()
    assert (me["email"], me["display_name"]) == (user.email, "Unchanged")


def test_delete_removes_the_account_its_sessions_and_its_items(
    api: httpx.Client, register_user: Callable[..., RegisteredUser], db: Database
) -> None:
    user = register_user()
    create_item(user.client, name="Owned by the deleted user")
    # Open tokens of both kinds; the delete must remove them too.
    api.post("/auth/password/reset", json={"email": user.email})
    user.client.post("/auth/email/verify")
    password_reset_token(db, user.id)
    email_verification_token(db, user.id)

    response = user.client.delete("/users/me")

    assert response.status_code == 204
    assert response.content == b""
    assert_error(user.client.get("/users/me"), 401, "invalid_session")
    assert_error(login(api, user.email, user.password), 401, "authentication_error")
    # No endpoint lists another user's rows; the database shows the cascade.
    for table in (
        "item",
        "session",
        "password_reset_token",
        "email_verification_token",
    ):
        count = db.fetch_one(
            f"SELECT count(*) FROM {table} WHERE user_id = %s", (user.id,)
        )
        assert count == (0,), table
    # The email is free again.
    again = api.post(
        "/auth/register", json={"email": user.email, "raw_password": "password-again"}
    )
    assert again.status_code == 201
