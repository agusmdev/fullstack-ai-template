"""Password reset: request a token, then set a new password with it.

Email delivery is not implemented, so tests read the emailed token from the
database (see helpers.password_reset_token).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.e2e.helpers import (
    EXPIRED,
    assert_error,
    create_passwordless_user,
    login,
    password_reset_token,
    unique_email,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    import httpx

    from tests.e2e.helpers import RegisteredUser
    from tests.e2e.stack import Database

GENERIC_REPLY = {"status": "success", "message": "Password reset email sent"}


def _count_tokens(db: Database, email: str) -> int:
    return db.fetch_one(
        'SELECT count(*) FROM password_reset_token t JOIN "user" u ON u.id = t.user_id '
        "WHERE u.email = %s",
        (email,),
    )[0]


def test_reset_sets_a_new_password_and_ends_old_sessions(
    api: httpx.Client, register_user: Callable[..., RegisteredUser], db: Database
) -> None:
    user = register_user()

    requested = api.post("/auth/password/reset", json={"email": user.email})
    assert requested.status_code == 200
    assert requested.json() == GENERIC_REPLY

    confirmed = api.post(
        "/auth/password/confirm",
        json={
            "token": password_reset_token(db, user.id),
            "new_password": "brand-new-pass",
        },
    )

    assert confirmed.status_code == 200
    assert confirmed.json() == {
        "status": "success",
        "message": "Password has been reset successfully",
    }
    assert_error(login(api, user.email, user.password), 401, "invalid_password")
    assert login(api, user.email, "brand-new-pass").status_code == 200
    # Every session that existed before the reset is revoked.
    assert_error(user.client.get("/users/me"), 401, "invalid_session")


def test_reset_token_works_only_once(
    api: httpx.Client, register_user: Callable[..., RegisteredUser], db: Database
) -> None:
    user = register_user()
    api.post("/auth/password/reset", json={"email": user.email})
    token = password_reset_token(db, user.id)
    first = api.post(
        "/auth/password/confirm", json={"token": token, "new_password": "first-new"}
    )
    assert first.status_code == 200

    second = api.post(
        "/auth/password/confirm", json={"token": token, "new_password": "second-new"}
    )

    assert_error(second, 400, "invalid_token", "Invalid or expired token")
    assert login(api, user.email, "first-new").status_code == 200


def test_a_new_request_invalidates_the_previous_token(
    api: httpx.Client, register_user: Callable[..., RegisteredUser], db: Database
) -> None:
    user = register_user()
    api.post("/auth/password/reset", json={"email": user.email})
    old_token = password_reset_token(db, user.id)
    api.post("/auth/password/reset", json={"email": user.email})
    new_token = password_reset_token(db, user.id)
    assert new_token != old_token

    old = api.post(
        "/auth/password/confirm",
        json={"token": old_token, "new_password": "from-the-old-token"},
    )
    new = api.post(
        "/auth/password/confirm",
        json={"token": new_token, "new_password": "from-the-new-token"},
    )

    assert_error(old, 400, "invalid_token")
    assert new.status_code == 200
    assert login(api, user.email, "from-the-new-token").status_code == 200
    assert_error(login(api, user.email, "from-the-old-token"), 401, "invalid_password")


def test_expired_token_is_rejected(
    api: httpx.Client, register_user: Callable[..., RegisteredUser], db: Database
) -> None:
    user = register_user()
    api.post("/auth/password/reset", json={"email": user.email})
    token = password_reset_token(db, user.id)
    db.execute(
        "UPDATE password_reset_token SET expires_at = %s WHERE id = %s",
        (EXPIRED, token),
    )

    response = api.post(
        "/auth/password/confirm", json={"token": token, "new_password": "never-set"}
    )

    assert_error(response, 400, "invalid_token")
    assert login(api, user.email, user.password).status_code == 200


def test_unknown_token_is_rejected(api: httpx.Client) -> None:
    response = api.post(
        "/auth/password/confirm",
        json={"token": "pr_does-not-exist", "new_password": "whatever"},
    )

    assert_error(response, 400, "invalid_token", "Invalid or expired token")


def test_unknown_email_gets_the_same_reply_and_no_token(
    api: httpx.Client, db: Database
) -> None:
    email = unique_email()

    response = api.post("/auth/password/reset", json={"email": email})

    # Same reply as for a real account, so the endpoint does not reveal emails.
    assert response.status_code == 200
    assert response.json() == GENERIC_REPLY
    assert _count_tokens(db, email) == 0


def test_account_without_password_gets_the_same_reply_and_no_token(
    api: httpx.Client, db: Database
) -> None:
    email = unique_email("oauth")
    create_passwordless_user(db, email)

    response = api.post("/auth/password/reset", json={"email": email})

    assert response.status_code == 200
    assert response.json() == GENERIC_REPLY
    assert _count_tokens(db, email) == 0


def test_new_password_must_have_8_characters(
    api: httpx.Client, register_user: Callable[..., RegisteredUser], db: Database
) -> None:
    user = register_user()
    api.post("/auth/password/reset", json={"email": user.email})
    token = password_reset_token(db, user.id)

    response = api.post(
        "/auth/password/confirm", json={"token": token, "new_password": "short-7"}
    )

    body = assert_error(response, 422, "validation_error")
    assert [issue["loc"] for issue in body["detail"]] == [["body", "new_password"]]
    # The token is still valid, and the old password still works.
    assert password_reset_token(db, user.id) == token
    assert login(api, user.email, user.password).status_code == 200


def test_reset_request_matches_the_email_in_any_case(
    api: httpx.Client, register_user: Callable[..., RegisteredUser], db: Database
) -> None:
    user = register_user()

    response = api.post("/auth/password/reset", json={"email": user.email.upper()})

    assert response.status_code == 200
    assert _count_tokens(db, user.email) == 1


def test_reset_request_validates_the_email(api: httpx.Client) -> None:
    response = api.post("/auth/password/reset", json={"email": "nope"})

    body = assert_error(response, 422, "validation_error")
    assert body["detail"][0]["loc"] == ["body", "email"]
