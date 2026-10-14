"""Automatic guards that keep this suite end-to-end. tests/conftest.py runs them.

Guard 1, end-to-end only: the run stops at collection, before Docker starts,
when
  - a test lives outside tests/e2e/ (there are no unit tests in this project),
  - a file under tests/ imports app code (tests talk to the live server only),
  - a test asks for a mocking fixture (BANNED_FIXTURES), or
  - a file under tests/, or any conftest.py of the backend, contains a mocking,
    patching, fake-server or in-process-app construct (BANNED_SOURCE).
Ruff's banned-api rule (TID251 in pyproject.toml) blocks the imports as well.

Guard 2, route coverage: after a full run, every route of the real app must
have received at least one successful (status < 400) request from the suite.
The server records each request it routes (its wide-event log line), so any
HTTP client counts. Routes that cannot succeed without a third party go in
ROUTE_COVERAGE_ALLOWLIST, each with its reason. KNOWN_GAPS lists covered
routes with a path no test can reach; every full run prints it.

This file is the only file under tests/ that may name the banned constructs
or import app code.
"""

from __future__ import annotations

import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterable

    from tests.e2e.stack import ServerLog

E2E_DIR = Path(__file__).resolve().parent
TESTS_DIR = E2E_DIR.parent
BACKEND_DIR = TESTS_DIR.parent


@dataclass
class RunState:
    """What the hooks in tests/conftest.py and the e2e fixtures share in a run."""

    # (method, route path, status) of every request the live server routed.
    route_hits: set[tuple[str, str, int]] = field(default_factory=set)
    deselected: int = 0
    # True once the live server answered; Guard 2 needs a stack that ran.
    stack_started: bool = False
    server_log: ServerLog | None = None
    coverage_problems: list[str] = field(default_factory=list)
    coverage_checked: bool = False


RUN_STATE = pytest.StashKey[RunState]()  # on config.stash
LOG_MARK = pytest.StashKey[int]()  # on item.stash: where the test's output starts

HOW_TO_TEST = (
    "Use the live-server fixtures in tests/e2e/conftest.py: `api`, `auth_client`, "
    "`register_user`, `make_client`. For state the public API cannot create "
    "(expired tokens, inactive users), use the `db` fixture."
)

# --- Guard 1: end-to-end only -------------------------------------------------

END_TO_END_ONLY = (
    "Tests talk to the live server over HTTP. Put them in "
    "tests/e2e/test_<feature>.py and do not import app code."
)

# `import app...` / `from app... import`: the app runs in its own process, so
# app code in a test is either a unit test or a patch with no effect.
APP_IMPORT = re.compile(r"^\s*(?:from|import)\s+app\b")

# pytest's default test file names.
TEST_FILE = re.compile(r"^(?:test_.*|.*_test)\.py$")

BANNED_FIXTURES: dict[str, str] = {
    "monkeypatch": "replaces real code or settings at runtime",
    "mocker": "pytest-mock",
    "class_mocker": "pytest-mock",
    "module_mocker": "pytest-mock",
    "package_mocker": "pytest-mock",
    "session_mocker": "pytest-mock",
    "httpx_mock": "pytest-httpx fakes HTTP",
    "respx_mock": "respx fakes HTTP",
    "requests_mock": "requests-mock fakes HTTP",
    "freezer": "freezegun fakes the clock",
    "time_machine": "time-machine fakes the clock",
    "httpserver": "a local fake server (pytest-httpserver, pytest-localserver)",
    "make_httpserver": "pytest-httpserver runs a fake server",
    "httpserver_listen_address": "pytest-httpserver runs a fake server",
    "httpsserver": "pytest-localserver runs a fake server",
    "vcr": "replays recorded HTTP (pytest-recording)",
    "vcr_config": "replays recorded HTTP (pytest-recording)",
    "vcr_cassette_dir": "replays recorded HTTP (pytest-recording)",
    "default_cassette_name": "replays recorded HTTP (pytest-recording)",
    "responses": "fakes HTTP (pytest-responses)",
    "aresponses": "fakes HTTP (aresponses)",
    "fs": "pyfakefs fakes the file system",
}

BANNED_SOURCE: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bdependency_overrides\b"), "replaces real FastAPI dependencies"),
    (
        re.compile(r"\bunittest\.mock\b|\bfrom\s+unittest\s+import\s+mock\b"),
        "mock library",
    ),
    (
        re.compile(r"\b(?:Magic|Async|NonCallable|Property)Mock\b|\bcreate_autospec\b"),
        "mock object",
    ),
    (
        re.compile(r"\bmock\.patch\b|\bpatch\.(?:object|dict|multiple)\b|@patch\b"),
        "patching",
    ),
    (
        re.compile(r"monkey_?patch", re.IGNORECASE),
        "replaces real code or settings at runtime",
    ),
    (re.compile(r"\bsetattr\s*\(|\bsys\.modules\b"), "patches code at runtime"),
    (re.compile(r"\bmocker\b"), "pytest-mock"),
    (re.compile(r"\bMock\b"), "mock object"),
    (
        re.compile(r"\b(?:ASGI|WSGI)Transport\b|\bTestClient\b"),
        "runs the app in-process instead of the live server",
    ),
    (
        re.compile(r"\b(?:Mock|Base|AsyncBase)Transport\b"),
        "fakes HTTP instead of sending it",
    ),
    (
        re.compile(r"\btransport\s*="),
        "a custom transport replaces the real network",
    ),
    (
        re.compile(r"\bvcr\b|\bcassette|\bhttpretty\b|\bpook\b|\bHTTPServer\b"),
        "fakes or replays HTTP",
    ),
    # A fake third party built with the project's own libraries. The real app
    # starts only in a child process (tests.e2e.run_server calls uvicorn.main()),
    # so no file under tests/ builds an app or starts a server itself.
    (
        re.compile(r"\b(?:FastAPI|Starlette|APIRouter)\s*\("),
        "builds an app in the tests: a fake server",
    ),
    (
        re.compile(
            r"\buvicorn\.(?:Server|Config|run)\b|\bfrom\s+uvicorn\b"
            r"|\b(?:hypercorn|daphne|granian|werkzeug|flask|bottle)\b"
        ),
        "starts a server in the tests: a fake server",
    ),
    (
        re.compile(
            r"\baiohttp\.web\b|\bfrom\s+aiohttp\s+import\s+web\b"
            r"|\bsocketserver\b|\bhttp\.server\b|\bwsgiref\b"
            r"|\b(?:start_server|create_server|serve_forever)\s*\(|\.listen\s*\("
        ),
        "accepts connections in the tests: a fake server",
    ),
    (re.compile(r"sqlite", re.IGNORECASE), "the template is Postgres-only"),
    (re.compile(r"\.create_all\("), "builds the schema without the migrations"),
]


def _backend_python_files() -> list[Path]:
    """Return every .py file of the backend, without virtualenvs and caches."""
    found: list[Path] = []
    for root, dirs, files in os.walk(BACKEND_DIR):
        # Skip .venv, .git, caches, and any other virtualenv.
        dirs[:] = sorted(
            d
            for d in dirs
            if not d.startswith((".", "__pycache__"))
            and d != "node_modules"
            and not (Path(root, d) / "pyvenv.cfg").exists()
        )
        found.extend(Path(root, name) for name in sorted(files) if name.endswith(".py"))
    return found


def _is_under(path: Path, directory: Path) -> bool:
    return path == directory or directory in path.parents


def find_mock_usage(items: Iterable[pytest.Item]) -> list[str]:
    """Return one line per Guard 1 problem: misplaced tests, app imports, mocks."""
    problems: list[str] = []
    for item in items:
        if not _is_under(Path(item.path).resolve(), E2E_DIR):
            problems.append(f"{item.nodeid}: a test outside tests/e2e/")
        requested = set(getattr(item, "fixturenames", ()))
        for name in sorted(requested & BANNED_FIXTURES.keys()):
            problems.append(
                f"{item.nodeid}: requests the `{name}` fixture ({BANNED_FIXTURES[name]})"
            )

    this_file = Path(__file__).resolve()
    for path in _backend_python_files():
        resolved = path.resolve()
        location = path.relative_to(BACKEND_DIR)
        if resolved == this_file:
            continue
        in_tests = _is_under(resolved, TESTS_DIR)
        if TEST_FILE.match(path.name) and not _is_under(resolved, E2E_DIR):
            problems.append(f"{location}: a test file outside tests/e2e/")
        # pytest loads every conftest.py from the rootdir down: scan them all.
        if not in_tests and path.name != "conftest.py":
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines, start=1):
            if in_tests and APP_IMPORT.match(line):
                problems.append(f"{location}:{number}: imports app code")
            for pattern, reason in BANNED_SOURCE:
                match = pattern.search(line)
                if match:
                    problems.append(f"{location}:{number}: `{match[0]}` ({reason})")
    return problems


def mock_usage_message(problems: list[str]) -> str:
    """Explain a Guard 1 failure."""
    return "\n".join(
        [
            "E2E guard: the backend tests run the real system only. Unit tests, "
            "app imports, mocks, patches, fake servers, dependency overrides and "
            "in-process apps are not allowed.",
            *(f"  {problem}" for problem in problems),
            END_TO_END_ONLY,
            HOW_TO_TEST,
        ]
    )


# --- Guard 2: route coverage ----------------------------------------------------

# (method, path template) -> why the route cannot get a successful response in
# this suite. Only for routes that need a third party for every success path.
# A route the guard cannot see (a WebSocket route, a Mount) also goes here,
# keyed by its kind ("WEBSOCKET", "MOUNT"), once a test covers it.
# The guard also fails when an entry is stale (route gone, or now covered).
ROUTE_COVERAGE_ALLOWLIST: dict[tuple[str, str], str] = {}

# (method, path template) -> a path of a covered route that no test can reach.
# Every full run prints this list, so the gaps stay visible.
KNOWN_GAPS: dict[tuple[str, str], str] = {
    ("GET", "/auth/oauth/{provider}/callback"): (
        "only the error redirects are tested; a successful Google sign-in "
        "(log in or create the user, the inactive_user redirect) needs "
        "Google's token endpoint"
    ),
}


def app_routes() -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    """Return the real app's HTTP routes and the routes the guard cannot see.

    Both are sets of (method, path template). HTTP routes are what the server
    logs a wide event for. Other kinds (WebSocket routes, Mounts) are keyed by
    their kind, for example ("WEBSOCKET", "/ws") or ("MOUNT", "/static").
    """
    from starlette.routing import Mount, Route, WebSocketRoute

    from app.main import create_app

    http: set[tuple[str, str]] = set()
    unseen: set[tuple[str, str]] = set()
    for route in create_app(add_sentry=False).routes:
        if isinstance(route, Route):
            methods = set(route.methods or ())
            if "GET" in methods:
                # Starlette adds HEAD to every GET route; it is not a separate API.
                methods.discard("HEAD")
            http.update((method, route.path) for method in methods)
        elif isinstance(route, WebSocketRoute):
            unseen.add(("WEBSOCKET", route.path))
        elif isinstance(route, Mount):
            unseen.add(("MOUNT", route.path))
        else:
            unseen.add((type(route).__name__.upper(), getattr(route, "path", "?")))
    return http, unseen


def route_coverage_problems(hits: Iterable[tuple[str, str, int]]) -> list[str]:
    """Return one line per app route without a successful e2e request."""
    succeeded: set[tuple[str, str]] = set()
    failed: dict[tuple[str, str], set[int]] = defaultdict(set)
    for method, path, status in hits:
        if status < 400:
            succeeded.add((method, path))
        else:
            failed[(method, path)].add(status)

    routes, unseen = app_routes()
    problems: list[str] = []
    for method, path in sorted(routes, key=lambda route: (route[1], route[0])):
        route = (method, path)
        if route in succeeded or route in ROUTE_COVERAGE_ALLOWLIST:
            continue
        statuses = failed.get(route)
        if statuses:
            codes = ", ".join(str(code) for code in sorted(statuses))
            problems.append(f"{method} {path}: only error responses ({codes})")
        else:
            problems.append(f"{method} {path}: never requested")
    for kind, path in sorted(unseen - ROUTE_COVERAGE_ALLOWLIST.keys()):
        problems.append(
            f"{kind} {path}: the guard cannot see this kind of route. Test it, then "
            f'add ("{kind}", "{path}") to ROUTE_COVERAGE_ALLOWLIST with the test name.'
        )
    for (method, path), _reason in sorted(ROUTE_COVERAGE_ALLOWLIST.items()):
        if (method, path) not in routes | unseen:
            problems.append(
                f"{method} {path}: in ROUTE_COVERAGE_ALLOWLIST, but the app has no "
                "such route. Remove the entry."
            )
        elif (method, path) in succeeded:
            problems.append(
                f"{method} {path}: in ROUTE_COVERAGE_ALLOWLIST, but the suite now "
                "covers it. Remove the entry."
            )
    for method, path in sorted(KNOWN_GAPS.keys() - routes):
        problems.append(
            f"{method} {path}: in KNOWN_GAPS, but the app has no such route. "
            "Remove the entry."
        )
    return problems


def known_gaps_message() -> str:
    """List the known untested paths (KNOWN_GAPS) for the terminal summary."""
    return "\n".join(
        [
            "Covered routes with paths no e2e test reaches (KNOWN_GAPS in "
            "tests/e2e/guards.py):",
            *(
                f"  {method} {path}: {reason}"
                for (method, path), reason in sorted(KNOWN_GAPS.items())
            ),
        ]
    )


def route_coverage_message(problems: list[str]) -> str:
    """Explain a Guard 2 failure."""
    return "\n".join(
        [
            "E2E route coverage: every app route needs at least one successful "
            "(status < 400) request in tests/e2e/.",
            *(f"  {problem}" for problem in problems),
            "Add a test in tests/e2e/test_<feature>.py that calls the route.",
            HOW_TO_TEST,
            "A route that cannot succeed without a third party goes in "
            "ROUTE_COVERAGE_ALLOWLIST (tests/e2e/guards.py) with the reason.",
        ]
    )


def is_full_run(config: pytest.Config, deselected: int) -> bool:
    """Return True when the whole e2e suite ran (no -k/-m/--lf/--ignore, no subset)."""
    if deselected:
        return False
    # --lf skips files and items at collection without pytest_deselected,
    # and --ignore/--ignore-glob drop files the same way.
    if config.getoption("lf", False):
        return False
    if config.getoption("ignore", None) or config.getoption("ignore_glob", None):
        return False
    # These options select tests but run none of them.
    if config.option.collectonly or config.option.setuponly or config.option.setupplan:
        return False
    invocation_dir = config.invocation_params.dir
    for arg in config.args:
        if "::" in arg:
            return False
        path = (invocation_dir / arg).resolve()
        if path != E2E_DIR and path not in E2E_DIR.parents:
            return False
    return True
