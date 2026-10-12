"""Small helpers for e2e tests: assertions and data set-up through the real API."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import httpx

    from tests.e2e.stack import Database

DEFAULT_PASSWORD = "correct-horse-battery-staple"
EXPIRED = "2000-01-01 00:00:00+00"
# JSON allows "\u0000" in strings; Postgres text cannot store it.
NUL = "\u0000"


@dataclass
class RegisteredUser:
    """A user created through POST /auth/register, logged in through POST /auth/login."""

    id: str
    email: str
    password: str
    display_name: str
    session_id: str
    client: httpx.Client


def unique_email(prefix: str = "user") -> str:
    """Return an email address no other test uses."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"


def assert_error(
    response: httpx.Response,
    status: int,
    error_code: str,
    detail: Any = None,
) -> dict[str, Any]:
    """Assert the API error contract: the status and a JSON ``{detail, error_code}``."""
    assert response.status_code == status, (
        f"expected {status}, got {response.status_code}: {response.text}"
    )
    body = response.json()
    assert set(body) == {"detail", "error_code"}, body
    assert body["error_code"] == error_code, body
    if detail is not None:
        assert body["detail"] == detail, body
    return body


def create_item(
    client: httpx.Client, name: str = "Item", description: str | None = None
) -> dict[str, Any]:
    """Create an item through POST /items and return the response body."""
    payload: dict[str, Any] = {"name": name}
    if description is not None:
        payload["description"] = description
    response = client.post("/items", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def login(api: httpx.Client, email: str, password: str) -> httpx.Response:
    """Call POST /auth/login and return the raw response."""
    return api.post("/auth/login", json={"email": email, "password": password})


# --- State the public API cannot create --------------------------------------
# Email delivery is not implemented, so the database is the "inbox": tests read
# emailed tokens from it. Expiry and deactivation have no endpoint either.


def password_reset_token(db: Database, user_id: str) -> str:
    """Return the user's newest unused password reset token (the emailed one)."""
    return db.fetch_one(
        "SELECT id FROM password_reset_token WHERE user_id = %s AND used_at IS NULL "
        "ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    )[0]


def email_verification_token(db: Database, user_id: str) -> str:
    """Return the user's newest unused email verification token (the emailed one)."""
    return db.fetch_one(
        "SELECT id FROM email_verification_token "
        "WHERE user_id = %s AND used_at IS NULL ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    )[0]


def deactivate_user(db: Database, user_id: str) -> None:
    """Set ``is_active = false`` (an admin action the API does not offer)."""
    assert db.execute('UPDATE "user" SET is_active = false WHERE id = %s', (user_id,))


def create_passwordless_user(db: Database, email: str) -> None:
    """Insert a user without a password, as Google sign-up creates one.

    The Google token exchange needs a third party, so the row is inserted
    directly.
    """
    db.execute(
        'INSERT INTO "user" '
        "(id, email, display_name, is_active, password, created_at, updated_at) "
        "VALUES (gen_random_uuid(), %s, 'OAuth User', true, NULL, now(), now())",
        (email,),
    )


def drop_server_connections(db: Database) -> None:
    """Make Postgres close every database connection of the live server (an outage).

    The server's next request that uses the database fails, like after a
    database restart or a network cut. (The server runs with the production
    default DB_POOL_PRE_PING=false, so it does not test connections first.)
    Send one successful request before this, so the server has connections.
    """
    rows = db.fetch_all(
        "SELECT pg_terminate_backend(pid, 5000) FROM pg_stat_activity "
        "WHERE datname = current_database() AND pid <> pg_backend_pid() "
        "AND backend_type = 'client backend'"
    )
    assert rows, "the server had no database connection to drop"
    assert all(terminated for (terminated,) in rows), rows
