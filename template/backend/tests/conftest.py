"""Suite-wide pytest hooks: the e2e guards, and server output on failures.

The fixtures are in tests/e2e/conftest.py; read that file first.

These hooks live here, one level above tests/e2e, because pytest loads this
file in every process (the pytest-xdist controller too, which never loads
tests/e2e/conftest.py) and for every test under tests/. The guard logic is in
tests/e2e/guards.py.
"""

from __future__ import annotations

import signal
import threading
from typing import TYPE_CHECKING, Any

import pytest

from tests.e2e.guards import (
    LOG_MARK,
    RUN_STATE,
    RunState,
    find_mock_usage,
    is_full_run,
    known_gaps_message,
    mock_usage_message,
    route_coverage_message,
    route_coverage_problems,
)

if TYPE_CHECKING:
    from collections.abc import Generator


def _interrupt_on_sigterm(signum: int, frame: Any) -> None:
    raise KeyboardInterrupt(f"stopped by signal {signum}")


def pytest_configure(config: pytest.Config) -> None:
    config.stash[RUN_STATE] = RunState()
    # SIGTERM (a CI cancel, `timeout`) stops the run like Ctrl+C: pytest then
    # runs the fixture teardown, which stops the server and the container.
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGTERM, _interrupt_on_sigterm)


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    # Guard 1: stop before any container starts if a test uses mocks.
    problems = find_mock_usage(items)
    if problems:
        raise pytest.UsageError(mock_usage_message(problems))


def pytest_deselected(items: list[pytest.Item]) -> None:
    if items:
        items[0].config.stash[RUN_STATE].deselected += len(items)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    # On failure, show what the server printed during the test.
    report = yield
    log = item.config.stash[RUN_STATE].server_log
    mark = item.stash.get(LOG_MARK, None)
    if report.failed and log is not None and mark is not None:
        output = log.render(mark)
        if output:
            report.sections.append(("Captured server output", output))
    return report


@pytest.hookimpl(optionalhook=True)
def pytest_testnodedown(node: object, error: object) -> None:
    # pytest-xdist controller: merge what each worker's server routed.
    output = getattr(node, "workeroutput", {})
    state = node.config.stash[RUN_STATE]  # type: ignore[attr-defined]
    state.route_hits.update(tuple(hit) for hit in output.get("e2e_route_hits", ()))
    state.deselected = max(state.deselected, output.get("e2e_deselected", 0))
    state.stack_started |= output.get("e2e_stack_started", False)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    config = session.config
    state = config.stash[RUN_STATE]
    workeroutput = getattr(config, "workeroutput", None)
    if workeroutput is not None:
        # pytest-xdist worker: the controller runs the guard on merged data.
        workeroutput["e2e_route_hits"] = sorted(state.route_hits)
        workeroutput["e2e_deselected"] = state.deselected
        workeroutput["e2e_stack_started"] = state.stack_started
        return
    if exitstatus not in (pytest.ExitCode.OK, pytest.ExitCode.TESTS_FAILED):
        return
    if session.shouldstop or session.shouldfail:
        return
    if not state.stack_started:
        # The stack never came up: the fixture error already explains why.
        return
    if not is_full_run(config, state.deselected):
        return
    # Guard 2: every app route got a successful request.
    state.coverage_checked = True
    state.coverage_problems = route_coverage_problems(state.route_hits)
    if state.coverage_problems:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter) -> None:
    state = terminalreporter.config.stash[RUN_STATE]
    if not state.coverage_checked:
        return
    if state.coverage_problems:
        terminalreporter.section("e2e route coverage", red=True, bold=True)
        terminalreporter.line(route_coverage_message(state.coverage_problems), red=True)
    terminalreporter.section("e2e known gaps", yellow=True)
    terminalreporter.line(known_gaps_message(), yellow=True)
