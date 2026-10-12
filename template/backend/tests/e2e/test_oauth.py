"""OAuth callback paths that need no third party.

Not covered (needs Google's token endpoint): a callback with a real ``code``
that logs in or creates the user, and the ``inactive_user`` redirect. See
KNOWN_GAPS in guards.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlsplit

from tests.e2e.stack import FRONTEND_URL

if TYPE_CHECKING:
    import httpx

    from tests.e2e.stack import Database, ServerLogView


def _redirect_target(response: httpx.Response) -> tuple[str, dict[str, list[str]]]:
    assert response.status_code == 302, response.text
    location = urlsplit(response.headers["location"])
    return f"{location.scheme}://{location.netloc}{location.path}", parse_qs(
        location.query
    )


def test_unsupported_provider_redirects_to_the_frontend_error_page(
    api: httpx.Client,
) -> None:
    response = api.get(
        "/auth/oauth/github/callback", params={"code": "abc", "state": "xyz"}
    )

    target, query = _redirect_target(response)
    assert target == f"{FRONTEND_URL}/oauth/error"
    assert query == {"error": ["unsupported_provider"]}


def test_provider_error_redirects_to_the_frontend_error_page(
    api: httpx.Client,
) -> None:
    # What Google sends when the user declines consent: no code, an error.
    response = api.get(
        "/auth/oauth/google/callback",
        params={"error": "access_denied", "state": "xyz"},
    )

    target, query = _redirect_target(response)
    assert target == f"{FRONTEND_URL}/oauth/error"
    assert query == {"error": ["access_denied"]}


def test_callback_without_code_redirects_to_the_frontend_error_page(
    api: httpx.Client,
) -> None:
    response = api.get("/auth/oauth/google/callback")

    target, query = _redirect_target(response)
    assert target == f"{FRONTEND_URL}/oauth/error"
    assert query == {"error": ["missing_code"]}


def test_provider_error_value_is_url_encoded(api: httpx.Client) -> None:
    response = api.get(
        "/auth/oauth/google/callback", params={"error": "bad&next=http://evil"}
    )

    _target, query = _redirect_target(response)
    assert query == {"error": ["bad&next=http://evil"]}


def test_failed_token_exchange_redirects_to_the_frontend_error_page(
    api: httpx.Client, db: Database, server_log: ServerLogView
) -> None:
    # The suite points Google's token endpoint at a closed local port (see
    # stack.UNREACHABLE_OAUTH_PROVIDER): the exchange fails like it does when
    # Google is down or rejects a used or expired code.
    response = api.get(
        "/auth/oauth/google/callback", params={"code": "abc", "state": "xyz"}
    )

    target, query = _redirect_target(response)
    assert target == f"{FRONTEND_URL}/oauth/error"
    assert query == {"error": ["provider_error"]}
    assert db.fetch_one('SELECT count(*) FROM "user"') == (0,)
    event = server_log.wide_event_for(response)
    assert event["custom"] == {"provider_failure": "ConnectionError"}
