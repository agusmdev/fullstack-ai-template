"""Wide events (one canonical log line per request) and secret redaction.

The server runs with LOG_FORMAT=json; ``server_log`` reads what it printed.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from tests.e2e.helpers import (
    assert_error,
    create_item,
    drop_server_connections,
    password_reset_token,
    unique_email,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    import httpx

    from tests.e2e.helpers import RegisteredUser
    from tests.e2e.stack import Database, ServerLogView


def test_each_request_emits_exactly_one_wide_event(
    register_user: Callable[..., RegisteredUser], server_log: ServerLogView
) -> None:
    user = register_user()

    response = user.client.post("/items", json={"name": "Logged"})
    item = response.json()

    event = server_log.wide_event_for(response)
    assert event["level"] == "INFO"
    assert event["method"] == "POST"
    assert event["path"] == "/items"
    assert event["status_code"] == 201
    assert event["duration_ms"] >= 0
    uuid.UUID(event["request_id"])
    assert event["user_id"] == user.id
    assert event["email"] == user.email
    assert event["action"] == "create"
    assert (event["entity_type"], event["entity_id"]) == ("item", item["id"])
    assert "entity_ids" not in event
    assert (event["service"], event["environment"]) == ("backend-e2e", "local")
    same_request = [
        e for e in server_log.events() if e.get("trace_id") == event["trace_id"]
    ]
    assert len(same_request) == 1


def test_wide_event_names_the_route_template(
    auth_client: httpx.Client, server_log: ServerLogView
) -> None:
    item = create_item(auth_client)

    response = auth_client.patch(f"/items/{item['id']}", json={"name": "Renamed"})

    event = server_log.wide_event_for(response)
    assert event["path"] == f"/items/{item['id']}"
    assert event["path_template"] == "/items/{item_id}"
    assert (event["action"], event["entity_type"]) == ("update", "item")
    assert event["entity_id"] == item["id"]


def test_client_errors_are_logged_as_warnings(
    auth_client: httpx.Client, server_log: ServerLogView
) -> None:
    response = auth_client.get(f"/items/{uuid.uuid4()}")
    assert response.status_code == 404

    event = server_log.wide_event_for(response)
    assert event["level"] == "WARNING"
    assert event["status_code"] == 404


def test_client_ip_comes_from_proxy_headers(
    api: httpx.Client, server_log: ServerLogView
) -> None:
    forwarded = api.get("/health", headers={"X-Forwarded-For": "203.0.113.7, 10.0.0.1"})
    real_ip = api.get("/health", headers={"X-Real-IP": "198.51.100.9"})
    direct = api.get("/health")

    assert server_log.wide_event_for(forwarded)["client_ip"] == "203.0.113.7"
    assert server_log.wide_event_for(real_ip)["client_ip"] == "198.51.100.9"
    assert server_log.wide_event_for(direct)["client_ip"] == "127.0.0.1"


def test_trace_id_header_wins_over_request_id(
    api: httpx.Client, server_log: ServerLogView
) -> None:
    trace_id = f"trace-{uuid.uuid4().hex}"

    api.get("/health", headers={"X-Trace-Id": trace_id})

    event = server_log.wait_for(lambda e: e.get("trace_id") == trace_id)
    assert event["path"] == "/health"


def test_sensitive_query_params_are_redacted(
    api: httpx.Client, server_log: ServerLogView
) -> None:
    secret = f"secret-{uuid.uuid4().hex}"

    response = api.get(
        "/auth/oauth/github/callback",
        params={"code": "c", "state": "s", "access_token": secret, "api_key": secret},
    )

    event = server_log.wide_event_for(response)
    # `code` is the one-time OAuth authorization code: a credential too.
    assert event["query_string"] == (
        "code=[REDACTED]&state=s&access_token=[REDACTED]&api_key=[REDACTED]"
    )
    # uvicorn's access line comes after the wide event; wait for it too.
    access_line = server_log.wait_for(
        lambda e: '"GET /auth/oauth/github/callback?' in e["message"]
    )
    assert (
        "code=[REDACTED]&state=s&access_token=[REDACTED]&api_key=[REDACTED]"
        in access_line["message"]
    )
    assert secret not in server_log.text()


def test_harmless_query_params_that_contain_code_are_kept(
    api: httpx.Client, server_log: ServerLogView
) -> None:
    response = api.get("/health", params={"error_code": "x", "zipcode": "12345"})

    event = server_log.wide_event_for(response)
    assert event["query_string"] == "error_code=x&zipcode=12345"


def test_credentials_never_reach_the_logs(
    api: httpx.Client,
    register_user: Callable[..., RegisteredUser],
    db: Database,
    server_log: ServerLogView,
) -> None:
    password = f"pw-{uuid.uuid4().hex}"
    new_password = f"new-pw-{uuid.uuid4().hex}"
    user = register_user(password=password)
    api.post("/auth/password/reset", json={"email": user.email})
    token = password_reset_token(db, user.id)
    api.post(
        "/auth/password/confirm", json={"token": token, "new_password": new_password}
    )
    last = api.post("/auth/login", json={"email": user.email, "password": new_password})
    server_log.wide_event_for(last)  # all earlier output has been read too

    output = server_log.text()
    for secret in (password, new_password, token, user.session_id, last.json()["id"]):
        assert secret not in output


def test_unhandled_error_is_logged_with_its_traceback(
    register_user: Callable[..., RegisteredUser],
    db: Database,
    server_log: ServerLogView,
) -> None:
    user = register_user()
    with drop_server_connections(db, user.client):
        response = user.client.get("/items")

    assert response.status_code == 500
    event = server_log.wide_event_for(response)
    assert event["level"] == "ERROR"
    assert (event["status_code"], event["error"]) == (500, True)
    assert event["error_type"]
    assert event["exception"]["type"] == event["error_type"]
    assert (event["method"], event["path"]) == ("GET", "/items")
    # The database error names the statement, never its parameter values.
    assert "[SQL parameters hidden" in event["error_message"]


def test_secrets_stay_out_of_the_logs_when_a_request_fails(
    api: httpx.Client,
    register_user: Callable[..., RegisteredUser],
    db: Database,
    server_log: ServerLogView,
) -> None:
    # A 500 logs a traceback and the database error. Neither may show the
    # values the request handled: passwords, password hashes, tokens.
    user = register_user(password=f"LoginSecret-{uuid.uuid4().hex}")
    api.post("/auth/password/reset", json={"email": user.email})
    token = password_reset_token(db, user.id)
    register_password = f"RegisterSecret-{uuid.uuid4().hex}"
    new_password = f"ResetSecret-{uuid.uuid4().hex}"

    requests = [
        ("/auth/login", {"email": user.email, "password": user.password}),
        (
            "/auth/register",
            {"email": unique_email(), "raw_password": register_password},
        ),
        ("/auth/password/confirm", {"token": token, "new_password": new_password}),
    ]
    for path, body in requests:
        # A successful request first, so the server holds a connection to drop.
        assert user.client.get("/users/me").status_code == 200
        with drop_server_connections(db, api):
            failed = api.post(path, json=body)
        assert_error(failed, 500, "internal_server_error")
        server_log.wide_event_for(failed)  # all its output has been read

    output = server_log.text()
    assert "Traceback" in output
    for secret in (user.password, register_password, new_password, token):
        assert secret not in output
    assert "$argon2" not in output
