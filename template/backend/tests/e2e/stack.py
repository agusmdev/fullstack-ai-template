"""The real stack the e2e suite drives: Postgres in Docker, Alembic migrations, uvicorn.

Nothing in this module is a fake:

- the database is the Postgres image from ``../docker-compose.yml`` (testcontainers);
- the schema comes from ``alembic upgrade head`` (the production migrations);
- the API is the production entry point, ``uvicorn --factory app.main:create_app``,
  in a child process configured only through environment variables
  (``run_server.py`` adds a watchdog: the server stops when the test run ends,
  also when it is killed).

Tests do not use this module directly. They use the fixtures in ``conftest.py``.
"""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from testcontainers.postgres import PostgresContainer

if TYPE_CHECKING:
    from collections.abc import Callable

BACKEND_DIR = Path(__file__).resolve().parents[2]
COMPOSE_FILE = BACKEND_DIR.parent / "docker-compose.yml"
FALLBACK_POSTGRES_IMAGE = "postgres:18.1-alpine"
E2E_DB_PASSWORD = "e2e-p@ss:w/rd#50%"

# The frontend origin the server is configured with. It is only a string the
# backend puts in redirects and CORS headers; no frontend runs in this suite.
FRONTEND_URL = "http://frontend.e2e.test"

# The suite has no Google. Its OAuth endpoints point at a closed local port, so
# a callback with a code fails the way it does when Google is down, and the
# suite never calls the real Google.
UNREACHABLE_OAUTH_PROVIDER = "https://127.0.0.1:1"

# Requests sent while waiting for the server to boot carry this request id, so
# they do not count as test coverage of GET /health.
READINESS_PROBE_ID = "e2e-readiness-probe"

STARTUP_TIMEOUT_S = 30.0
# The server's SQLAlchemy pool size (DB_POOL_SIZE).
SERVER_DB_POOL_SIZE = 5

# One wide event (canonical log line) is emitted per request with this message.
WIDE_EVENT_MESSAGE = "request_completed"


def postgres_image() -> str:
    """Return the Postgres image of the ``db`` service in docker-compose.yml."""
    if COMPOSE_FILE.is_file():
        match = re.search(
            r"^\s*image:\s*[\"']?(postgres:[^\s\"']+)",
            COMPOSE_FILE.read_text(),
            re.MULTILINE,
        )
        if match:
            return match.group(1)
    return FALLBACK_POSTGRES_IMAGE


def start_postgres() -> PostgresContainer:
    """Start a throwaway Postgres container (testcontainers removes it at exit)."""
    image = postgres_image()
    try:
        # The password has characters that DB_URL must URL-encode ("@:/#%"), so
        # every run proves the app and Alembic read an encoded password.
        container = PostgresContainer(
            image, username="app", password=E2E_DB_PASSWORD, dbname="app", driver=None
        )
        container.start()
    except Exception as exc:
        raise RuntimeError(
            f"Could not start the e2e Postgres container ({image}). "
            "The backend tests need a running Docker daemon: check `docker ps`."
        ) from exc
    return container


def server_environment(db_url: str) -> dict[str, str]:
    """Return the environment for the app process: real settings, no test hooks.

    The settings the suite depends on are set explicitly. Environment
    variables win over ``.env``, so a developer's ``.env`` cannot change them.
    """
    return {
        **os.environ,
        "PYTHONUNBUFFERED": "1",
        "DB_URL": db_url,
        "DB_POOL_SIZE": str(SERVER_DB_POOL_SIZE),
        "DB_POOL_PRE_PING": "false",
        "APP_NAME": "backend-e2e",
        # "local" makes create_app() leave Sentry off.
        "ENVIRONMENT": "local",
        "DEBUG_MODE": "false",
        # DEBUG so the "no secrets in the logs" tests also see debug lines.
        "LOG_LEVEL": "DEBUG",
        # JSON lines on stdout: the suite parses them (see ServerLog).
        "LOG_FORMAT": "json",
        "FRONTEND_URL": FRONTEND_URL,
        "SENTRY_DSN": "",
        "GOOGLE_CLIENT_ID": "e2e-client-id",
        "GOOGLE_CLIENT_SECRET": "e2e-client-secret",
        "GOOGLE_TOKEN_URL": f"{UNREACHABLE_OAUTH_PROVIDER}/token",
        "GOOGLE_USER_INFO_URL": f"{UNREACHABLE_OAUTH_PROVIDER}/userinfo",
    }


def _alembic(env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def run_migrations(env: dict[str, str]) -> None:
    """Apply the real migrations, then fail if the models need a new migration.

    ``alembic upgrade head`` builds the schema. ``alembic check`` then compares
    it with the SQLAlchemy models: a model change without a migration fails
    the whole suite here, with Alembic's list of the missing operations.
    """
    upgrade = _alembic(env, "upgrade", "head")
    if upgrade.returncode != 0:
        raise RuntimeError(
            "`alembic upgrade head` failed against the e2e database:\n"
            f"{upgrade.stdout}\n{upgrade.stderr}"
        )
    check = _alembic(env, "check")
    if check.returncode != 0:
        raise RuntimeError(
            "The SQLAlchemy models and the migrations disagree (`alembic check`).\n"
            "Generate a migration: "
            'uv run alembic revision --autogenerate -m "describe the change"\n'
            f"{check.stdout}\n{check.stderr}"
        )


class Database:
    """Direct SQL access to the e2e database (autocommit, one connection)."""

    def __init__(self, url: str) -> None:
        self.url = url
        self._conn = psycopg.connect(url, autocommit=True)
        # A request that is still finishing can hold a lock for a few
        # milliseconds. Never wait forever for it.
        self._conn.execute("SET lock_timeout = '10s'")
        self._tables: list[str] | None = None

    def application_tables(self) -> list[str]:
        """Return every table the migrations created, except ``alembic_version``."""
        if self._tables is None:
            rows = self.fetch_all(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename <> 'alembic_version' "
                "ORDER BY tablename"
            )
            self._tables = [row[0] for row in rows]
        return self._tables

    def truncate_all(self) -> None:
        """Empty every application table; the schema and alembic_version stay."""
        tables = self.application_tables()
        if not tables:
            return
        statement = sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
            sql.SQL(", ").join(sql.Identifier(table) for table in tables)
        )
        self._conn.execute(statement)

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> int:
        """Run one statement and return the number of affected rows."""
        cursor = self._conn.execute(query, params)  # type: ignore[arg-type]
        return cursor.rowcount

    def fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> tuple[Any, ...]:
        """Run a query that must return exactly one row and return that row."""
        rows = self.fetch_all(query, params)
        assert len(rows) == 1, f"expected exactly one row, got {len(rows)}: {query}"
        return rows[0]

    def fetch_all(
        self, query: str, params: tuple[Any, ...] = ()
    ) -> list[tuple[Any, ...]]:
        """Run a query and return all rows."""
        return self._conn.execute(query, params).fetchall()  # type: ignore[arg-type]

    def allow_connections(self, allow: bool) -> None:
        """Let new connections to this database in, or turn them away.

        Open connections, such as this object's own, stay. Postgres does not
        change this for the current database, so it goes through ``postgres``.
        """
        name = self.fetch_one("SELECT current_database()")[0]
        conninfo = make_conninfo(self.url, dbname="postgres")
        with psycopg.connect(conninfo, autocommit=True) as conn:
            conn.execute(
                sql.SQL("ALTER DATABASE {} WITH ALLOW_CONNECTIONS {}").format(
                    sql.Identifier(name), sql.Literal(allow)
                )
            )

    def close(self) -> None:
        """Close the connection."""
        self._conn.close()


# Keys left out of ServerLog.render(): shown elsewhere or the same on every line.
_RENDER_SKIP = frozenset({"level", "message", "service", "environment", "timestamp"})


def _parse_event(line: str) -> dict[str, Any] | None:
    """Turn one loguru JSON line into a flat event dict, or None for other output."""
    if not line.startswith("{"):
        return None
    try:
        record = json.loads(line)["record"]
    except (ValueError, KeyError, TypeError):
        return None
    event: dict[str, Any] = dict(record.get("extra") or {})
    event["level"] = record["level"]["name"]
    event["message"] = record["message"]
    if record.get("exception"):
        event["exception"] = record["exception"]
    return event


class ServerLog:
    """Everything the server process prints, captured line by line (thread-safe).

    The app logs JSON (LOG_FORMAT=json), so each loguru line is also parsed into
    an event dict: ``{"level", "message", **extra}``. The wide event of a
    request has ``message == "request_completed"``.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._lines: list[str] = []
        self._events: list[tuple[int, dict[str, Any]]] = []
        # (method, route path, status) of every request the server routed.
        self.route_hits: set[tuple[str, str, int]] = set()

    def feed(self, line: str) -> None:
        """Store one output line from the server process."""
        event = _parse_event(line)
        with self._lock:
            index = len(self._lines)
            self._lines.append(line)
            if event is None:
                return
            self._events.append((index, event))
            if (
                event["message"] == WIDE_EVENT_MESSAGE
                and event.get("trace_id") != READINESS_PROBE_ID
            ):
                route = event.get("path_template") or event.get("path", "")
                self.route_hits.add(
                    (event.get("method", ""), route, int(event.get("status_code", 0)))
                )

    def mark(self) -> int:
        """Return a position; pass it as ``since`` to read only newer output."""
        with self._lock:
            return len(self._lines)

    def lines(self, since: int = 0) -> list[str]:
        """Return the raw output lines printed after ``since``."""
        with self._lock:
            return self._lines[since:]

    def events(self, since: int = 0) -> list[dict[str, Any]]:
        """Return the parsed log events printed after ``since``."""
        with self._lock:
            return [event for index, event in self._events if index >= since]

    def wait_for(
        self,
        predicate: Callable[[dict[str, Any]], bool],
        *,
        since: int = 0,
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        """Wait until an event after ``since`` matches ``predicate`` and return it.

        Output arrives through a pipe, so it can lag the HTTP response by a
        few milliseconds.
        """
        deadline = time.monotonic() + timeout
        while True:
            for event in self.events(since):
                if predicate(event):
                    return event
            if time.monotonic() > deadline:
                raise AssertionError(
                    f"no server log event matched within {timeout}s; events seen:\n"
                    + "\n".join(json.dumps(e, default=str) for e in self.events(since))
                )
            time.sleep(0.02)

    def render(self, since: int = 0) -> str:
        """Return the output after ``since`` in a compact, readable form."""
        rendered = []
        for line in self.lines(since):
            event = _parse_event(line)
            if event is None:
                rendered.append(line)
                continue
            extra = {k: v for k, v in event.items() if k not in _RENDER_SKIP}
            rendered.append(
                f"{event['level']} {event['message']} {json.dumps(extra, default=str)}"
            )
        return "\n".join(rendered)


class ServerLogView:
    """The part of the server output printed during one test."""

    def __init__(self, log: ServerLog, since: int) -> None:
        self._log = log
        self._since = since

    def lines(self) -> list[str]:
        """Return the raw output lines (JSON for loguru records)."""
        return self._log.lines(self._since)

    def text(self) -> str:
        """Return the raw output as one string."""
        return "\n".join(self.lines())

    def events(self) -> list[dict[str, Any]]:
        """Return the parsed log events: ``{"level", "message", **extra}``."""
        return self._log.events(self._since)

    def wait_for(
        self, predicate: Callable[[dict[str, Any]], bool], timeout: float = 5.0
    ) -> dict[str, Any]:
        """Wait for an event that matches ``predicate`` and return it."""
        return self._log.wait_for(predicate, since=self._since, timeout=timeout)

    def wide_event_for(self, response: httpx.Response) -> dict[str, Any]:
        """Return the wide event (one per request) the server logged for ``response``.

        Fixture clients send a unique ``x-request-id``; the server logs it as
        ``trace_id``.
        """
        request_id = response.request.headers["x-request-id"]
        return self.wait_for(
            lambda event: event["message"] == WIDE_EVENT_MESSAGE
            and event.get("trace_id") == request_id
        )


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class LiveServer:
    """The real app, served by uvicorn in a child process on a free port."""

    def __init__(self, env: dict[str, str]) -> None:
        self.env = env
        self.log = ServerLog()
        self.port = 0
        self.base_url = ""
        self._process: subprocess.Popen[str] | None = None
        self._reader: threading.Thread | None = None

    def start(self, attempts: int = 3) -> None:
        """Start uvicorn and wait until GET /health answers 200."""
        for _ in range(attempts):
            self.port = _free_port()
            self.base_url = f"http://127.0.0.1:{self.port}"
            self._spawn()
            if self._wait_until_ready():
                return
            self.stop()  # also waits until all output is read
            # Another process can take the free port before uvicorn binds it.
            if "address already in use" not in "\n".join(self.log.lines()).lower():
                break
        raise RuntimeError(
            "The app did not start (uvicorn app.main:create_app). Server output:\n"
            + "\n".join(self.log.lines())
        )

    def _spawn(self) -> None:
        # The Dockerfile CMD (uvicorn --factory app.main:create_app), bound to
        # localhost, through run_server.py: it stops the server when stdin
        # closes, which happens when this process ends in any way.
        self._process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "tests.e2e.run_server",
                "--factory",
                "app.main:create_app",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
            ],
            cwd=BACKEND_DIR,
            env=self.env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        process = self._process

        def _pump() -> None:
            assert process.stdout is not None
            for line in process.stdout:
                self.log.feed(line.rstrip("\n"))

        self._reader = threading.Thread(
            target=_pump, name="e2e-server-log", daemon=True
        )
        self._reader.start()

    def _wait_until_ready(self) -> bool:
        assert self._process is not None
        deadline = time.monotonic() + STARTUP_TIMEOUT_S
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                return False
            try:
                response = httpx.get(
                    f"{self.base_url}/health",
                    headers={"x-request-id": READINESS_PROBE_ID},
                    timeout=1.0,
                )
                if response.status_code == 200:
                    return True
            except httpx.TransportError:
                pass
            time.sleep(0.1)
        return False

    def stop(self) -> None:
        """Stop uvicorn gracefully (SIGTERM), then wait for the output pump."""
        if self._process is None:
            return
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)
        if self._process.stdin is not None:
            self._process.stdin.close()
        if self._reader is not None:
            self._reader.join(timeout=5)
        self._process = None
        self._reader = None
