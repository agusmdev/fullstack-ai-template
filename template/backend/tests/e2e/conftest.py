"""Backend end-to-end suite: the fixtures. Start reading here.

The suite runs the real system:

  Postgres (the docker-compose.yml image, started with testcontainers)
    -> ``alembic upgrade head`` and ``alembic check``
    -> the real app (``uvicorn --factory app.main:create_app``) in a child process
    -> tests send real HTTP requests with httpx.

Run it with ``uv run pytest`` (Docker must be running).

How to add a test
-----------------
Put it in ``tests/e2e/test_<feature>.py``. Tests are plain sync functions that
use the fixtures below and assert on real outcomes (follow-up GETs)::

    from tests.e2e.helpers import create_item

    def test_rename_item(auth_client):
        item = create_item(auth_client, name="Old")
        response = auth_client.patch(f"/items/{item['id']}", json={"name": "New"})
        assert response.status_code == 200
        assert auth_client.get(f"/items/{item['id']}").json()["name"] == "New"

Fixtures
--------
``api``            anonymous httpx client for the live server
``auth_client``    client of a freshly registered and logged-in user
``register_user``  factory: ``register_user(email=..., password=...)`` returns a
                   ``RegisteredUser`` (``.client``, ``.id``, ``.email``, ...)
``make_client``    factory: ``make_client(token=None)`` returns a new client
``server_log``     the server output during this test (``.wide_event_for(response)``)
``db``             raw SQL, only for state the public API cannot create
``server``         (session) the live server: ``.base_url``, ``.log``

Helpers for assertions and set-up live in ``tests/e2e/helpers.py``.

Rules the run enforces (``tests/e2e/guards.py``, hooked in ``tests/conftest.py``)
------------------------------------------------------------------------------
- End-to-end only: tests live in ``tests/e2e/`` and do not import app code.
- No mocks, patches, fake servers, dependency overrides or in-process apps.
- Every app route gets at least one successful request somewhere in the suite.
- The models and the migrations agree (``alembic check``).

Failure paths are real too: ``with helpers.drop_server_connections(db, client):``
cuts the server off from Postgres (an outage), and the suite's Google
endpoints are a closed local port (Google is down).

Every test starts with empty tables: all application tables are truncated
before each test, so tests pass in any order.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, NoReturn

import httpx
import pytest

from tests.e2e.guards import LOG_MARK, RUN_STATE
from tests.e2e.helpers import DEFAULT_PASSWORD, RegisteredUser, unique_email
from tests.e2e.stack import (
    Database,
    LiveServer,
    ServerLogView,
    run_migrations,
    server_environment,
    start_postgres,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


def _stop_the_run(exc: RuntimeError) -> NoReturn:
    # One clear message instead of the same error for every test.
    cause = f"\nCause: {exc.__cause__!r}" if exc.__cause__ else ""
    pytest.exit(f"{exc}{cause}", returncode=pytest.ExitCode.INTERNAL_ERROR)


@pytest.fixture(scope="session")
def database() -> Iterator[Database]:
    """(session) Real Postgres with the real migrations applied."""
    try:
        container = start_postgres()
    except RuntimeError as exc:
        _stop_the_run(exc)
    try:
        url = container.get_connection_url()
        try:
            run_migrations(server_environment(url))
        except RuntimeError as exc:
            _stop_the_run(exc)
        handle = Database(url)
        try:
            yield handle
        finally:
            handle.close()
    finally:
        container.stop()


@pytest.fixture(scope="session")
def server(database: Database, pytestconfig: pytest.Config) -> Iterator[LiveServer]:
    """(session) The real app, served by uvicorn on a free port."""
    live = LiveServer(server_environment(database.url))
    try:
        live.start()
    except RuntimeError as exc:
        _stop_the_run(exc)
    state = pytestconfig.stash[RUN_STATE]
    state.server_log = live.log
    state.stack_started = True
    try:
        yield live
    finally:
        live.stop()
        state.route_hits |= live.log.route_hits


@pytest.fixture(autouse=True)
def _isolated_test(
    request: pytest.FixtureRequest, database: Database, server: LiveServer
) -> None:
    """Empty every application table and mark where this test's server output starts."""
    database.truncate_all()
    request.node.stash[LOG_MARK] = server.log.mark()


@pytest.fixture
def db(database: Database) -> Database:
    """Raw SQL on the test database, only for state the public API cannot create."""
    return database


def _tag_request(request: httpx.Request) -> None:
    # The server logs this header as `trace_id` in the request's wide event.
    if "x-request-id" not in request.headers:
        request.headers["x-request-id"] = uuid.uuid4().hex


@pytest.fixture
def make_client(server: LiveServer) -> Iterator[Callable[..., httpx.Client]]:
    """Factory: ``make_client(token=None)`` returns an httpx client for the live server."""
    clients: list[httpx.Client] = []

    def _make(token: str | None = None) -> httpx.Client:
        client = httpx.Client(
            base_url=server.base_url,
            headers={"Authorization": f"Bearer {token}"} if token else None,
            timeout=15.0,
            event_hooks={"request": [_tag_request]},
        )
        clients.append(client)
        return client

    yield _make
    for client in clients:
        client.close()


@pytest.fixture
def api(make_client: Callable[..., httpx.Client]) -> httpx.Client:
    """Anonymous httpx client for the live server."""
    return make_client()


@pytest.fixture
def register_user(
    api: httpx.Client, make_client: Callable[..., httpx.Client]
) -> Callable[..., RegisteredUser]:
    """Factory: register and log in a user through the API; returns a RegisteredUser."""

    def _register(
        *,
        email: str | None = None,
        password: str = DEFAULT_PASSWORD,
        display_name: str = "E2E User",
    ) -> RegisteredUser:
        email = email or unique_email()
        registered = api.post(
            "/auth/register",
            json={
                "email": email,
                "raw_password": password,
                "display_name": display_name,
            },
        )
        assert registered.status_code == 201, registered.text
        logged_in = api.post("/auth/login", json={"email": email, "password": password})
        assert logged_in.status_code == 200, logged_in.text
        session_id = logged_in.json()["id"]
        client = make_client(session_id)
        me = client.get("/users/me")
        assert me.status_code == 200, me.text
        return RegisteredUser(
            id=me.json()["id"],
            email=email,
            password=password,
            display_name=display_name,
            session_id=session_id,
            client=client,
        )

    return _register


@pytest.fixture
def auth_client(register_user: Callable[..., RegisteredUser]) -> httpx.Client:
    """httpx client of a freshly registered and logged-in user."""
    return register_user().client


@pytest.fixture
def server_log(request: pytest.FixtureRequest, server: LiveServer) -> ServerLogView:
    """The server output printed during this test (wide events are parsed)."""
    return ServerLogView(server.log, request.node.stash[LOG_MARK])
