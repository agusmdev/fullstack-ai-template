"""Email verification: request a token (authenticated), then confirm it.

Email delivery is not implemented, so tests read the emailed token from the
database (see helpers.email_verification_token).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from tests.e2e.helpers import EXPIRED, assert_error, email_verification_token

if TYPE_CHECKING:
    from collections.abc import Callable

    import httpx

    from tests.e2e.helpers import RegisteredUser
    from tests.e2e.stack import Database


def test_new_user_is_not_verified(auth_client: httpx.Client) -> None:
    me = auth_client.get("/users/me").json()

    assert me["is_email_verified"] is False
    assert me["email_verified_at"] is None


def test_confirming_the_emailed_token_verifies_the_email(
    api: httpx.Client, register_user: Callable[..., RegisteredUser], db: Database
) -> None:
    user = register_user()

    requested = user.client.post("/auth/email/verify")
    assert requested.status_code == 200
    assert requested.json() == {
        "status": "success",
        "message": "Verification email sent",
    }

    confirmed = api.post(
        "/auth/email/verify/confirm",
        json={"token": email_verification_token(db, user.id)},
    )

    assert confirmed.status_code == 200
    assert confirmed.json() == {
        "status": "success",
        "message": "Email has been verified successfully",
    }
    me = user.client.get("/users/me").json()
    assert me["is_email_verified"] is True
    assert datetime.fromisoformat(me["email_verified_at"]).tzinfo is not None


def test_verified_user_cannot_request_another_token(
    api: httpx.Client, register_user: Callable[..., RegisteredUser], db: Database
) -> None:
    user = register_user()
    user.client.post("/auth/email/verify")
    api.post(
        "/auth/email/verify/confirm",
        json={"token": email_verification_token(db, user.id)},
    )

    response = user.client.post("/auth/email/verify")

    assert_error(response, 400, "email_already_verified", "Email is already verified")


def test_verification_token_works_only_once(
    api: httpx.Client, register_user: Callable[..., RegisteredUser], db: Database
) -> None:
    user = register_user()
    user.client.post("/auth/email/verify")
    token = email_verification_token(db, user.id)
    assert (
        api.post("/auth/email/verify/confirm", json={"token": token}).status_code == 200
    )

    verified_at = user.client.get("/users/me").json()["email_verified_at"]

    again = api.post("/auth/email/verify/confirm", json={"token": token})

    assert_error(again, 400, "invalid_token", "Invalid or expired token")
    # The failed second use changes nothing.
    me = user.client.get("/users/me").json()
    assert me["is_email_verified"] is True
    assert me["email_verified_at"] == verified_at


def test_a_new_request_invalidates_the_previous_token(
    api: httpx.Client, register_user: Callable[..., RegisteredUser], db: Database
) -> None:
    user = register_user()
    user.client.post("/auth/email/verify")
    old_token = email_verification_token(db, user.id)
    user.client.post("/auth/email/verify")

    response = api.post("/auth/email/verify/confirm", json={"token": old_token})

    assert_error(response, 400, "invalid_token")
    assert user.client.get("/users/me").json()["is_email_verified"] is False


def test_expired_token_is_rejected(
    api: httpx.Client, register_user: Callable[..., RegisteredUser], db: Database
) -> None:
    user = register_user()
    user.client.post("/auth/email/verify")
    token = email_verification_token(db, user.id)
    db.execute(
        "UPDATE email_verification_token SET expires_at = %s WHERE id = %s",
        (EXPIRED, token),
    )

    response = api.post("/auth/email/verify/confirm", json={"token": token})

    assert_error(response, 400, "invalid_token")
    assert user.client.get("/users/me").json()["is_email_verified"] is False


def test_unknown_token_is_rejected(api: httpx.Client) -> None:
    response = api.post(
        "/auth/email/verify/confirm", json={"token": "ev_does-not-exist"}
    )

    assert_error(response, 400, "invalid_token", "Invalid or expired token")
