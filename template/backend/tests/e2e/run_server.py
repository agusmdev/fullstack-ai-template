"""Run uvicorn like the Dockerfile does, and stop it when the test run is gone.

``python -m tests.e2e.run_server <uvicorn arguments>`` is ``uvicorn <uvicorn
arguments>`` plus one watchdog: the test process holds the write end of this
process's stdin. When the test process ends in any way (also SIGKILL, a CI
cancel or a timeout), the operating system closes that pipe, stdin reaches
end-of-file, and the server shuts down. No orphan server outlives a run.

The app is the real one: uvicorn imports ``app.main:create_app`` itself.
"""

from __future__ import annotations

import os
import signal
import sys
import threading
import time

import uvicorn

# After SIGTERM, uvicorn shuts down gracefully. Exit hard if that hangs.
SHUTDOWN_GRACE_S = 10.0


def _stop_when_the_test_run_is_gone() -> None:
    sys.stdin.buffer.read()  # returns at end-of-file only
    os.kill(os.getpid(), signal.SIGTERM)
    time.sleep(SHUTDOWN_GRACE_S)
    os._exit(1)


if __name__ == "__main__":
    threading.Thread(
        target=_stop_when_the_test_run_is_gone, name="e2e-watchdog", daemon=True
    ).start()
    uvicorn.main()
