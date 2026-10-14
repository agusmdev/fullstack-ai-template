#!/usr/bin/env bash
# Starts one piece of the real e2e stack: `stack.sh db|backend|frontend`.
#
# playwright.config.ts runs this through `webServer` and passes the settings
# from e2e/support/stack.ts as environment variables. Run the suite with
# `bun run test:e2e`; do not start this script by hand.
#
# Each piece stops when Playwright stops it (SIGTERM) and also when the
# Playwright runner process is gone (E2E_RUNNER_PID). A killed test run must not
# leave a container or a server on the e2e ports.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
frontend_dir="$(cd "$here/../.." && pwd)"
backend_dir="$(cd "$frontend_dir/../backend" && pwd)"

# Block while process $1 runs and the Playwright runner is alive.
# Returns the exit status of $1 when it stops by itself.
supervise() {
  local pid=$1
  while kill -0 "$pid" 2>/dev/null; do
    kill -0 "$E2E_RUNNER_PID" 2>/dev/null || return 0
    sleep 1 &
    wait $! # in the background, so a SIGTERM does not print "Terminated"
  done
  wait "$pid"
}

# On SIGTERM/SIGINT, exit through the EXIT trap, which does the cleanup.
trap 'exit 143' TERM INT

require() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "e2e: '$1' is required to $2, and it is not on the PATH." >&2
    exit 1
  }
}

db_is_ready() {
  # Over TCP inside the container: the image's first-boot init server listens
  # on the Unix socket only, so TCP answers only when the real server is up.
  docker exec "$E2E_DB_CONTAINER" pg_isready --quiet --host 127.0.0.1 --username app --dbname app \
    >/dev/null 2>&1
}

backend_port_is_open() {
  (exec 3<>"/dev/tcp/127.0.0.1/${E2E_BACKEND_PORT}") 2>/dev/null
}

start_db() {
  require docker "run the e2e Postgres container"
  # With E2E_REUSE=1 (never in CI), playwright.config.ts reuses an e2e backend
  # that is already running. That backend uses the running e2e database, so
  # keep it, and leave it to whoever started it.
  if [ -n "${E2E_REUSE:-}" ] && backend_port_is_open && db_is_ready; then
    echo "e2e db ready on 127.0.0.1:${E2E_DB_PORT} (reused)"
    docker wait "$E2E_DB_CONTAINER" >/dev/null &
    supervise $!
    return
  fi

  # A container with this name belongs to another test run (maybe from another
  # checkout) while the runner that started it is alive. Never remove it.
  local owner
  owner="$(docker inspect --format '{{ index .Config.Labels "e2e.runner-pid" }}' \
    "$E2E_DB_CONTAINER" 2>/dev/null || true)"
  if [ -n "$owner" ] && [ "$owner" != "$E2E_RUNNER_PID" ] && kill -0 "$owner" 2>/dev/null; then
    echo "e2e db: container $E2E_DB_CONTAINER is in use by another test run (pid $owner)." >&2
    echo "Wait for it to finish, or set E2E_DB_PORT, E2E_BACKEND_PORT and E2E_FRONTEND_PORT" >&2
    echo "to other free ports to run both at the same time." >&2
    exit 1
  fi

  remove_container() { docker rm -f "$E2E_DB_CONTAINER" >/dev/null 2>&1 || true; }
  remove_container # a container left by a run that was killed hard
  trap remove_container EXIT

  # tmpfs storage: every run starts with an empty database.
  # fsync and friends are off because the data is thrown away anyway.
  docker run --detach --rm --name "$E2E_DB_CONTAINER" \
    --label "e2e.runner-pid=$E2E_RUNNER_PID" --label "e2e.checkout=$frontend_dir" \
    --env POSTGRES_USER=app --env POSTGRES_PASSWORD=app --env POSTGRES_DB=app \
    --publish "127.0.0.1:${E2E_DB_PORT}:5432" \
    --tmpfs /var/lib/postgresql \
    "$E2E_DB_IMAGE" \
    -c fsync=off -c synchronous_commit=off -c full_page_writes=off >/dev/null

  for _ in $(seq 1 120); do
    if db_is_ready; then
      echo "e2e db ready on 127.0.0.1:${E2E_DB_PORT}"
      docker wait "$E2E_DB_CONTAINER" >/dev/null &
      supervise $!
      return
    fi
    sleep 0.5
  done
  echo "e2e db: Postgres did not become ready" >&2
  docker logs "$E2E_DB_CONTAINER" >&2 || true
  exit 1
}

start_backend() {
  require uv "run the backend (https://docs.astral.sh/uv/)"
  cd "$backend_dir"
  # Alembic logs every step; show that only when the migration fails.
  local migrate_log
  migrate_log="$(mktemp)"
  if ! uv run --frozen alembic upgrade head >"$migrate_log" 2>&1; then
    cat "$migrate_log" >&2
    rm -f "$migrate_log"
    echo "e2e backend: 'alembic upgrade head' failed (output above)." >&2
    exit 1
  fi
  rm -f "$migrate_log"
  uv run --frozen uvicorn --factory app.main:create_app \
    --host 127.0.0.1 --port "$E2E_BACKEND_PORT" --log-level warning &
  server=$!
  trap 'kill -TERM "$server" 2>/dev/null || true; wait "$server" 2>/dev/null || true' EXIT
  supervise "$server"
}

start_frontend() {
  cd "$frontend_dir"
  ./node_modules/.bin/vite dev --host 127.0.0.1 --port "$E2E_FRONTEND_PORT" --strictPort &
  server=$!
  trap 'kill -TERM "$server" 2>/dev/null || true; wait "$server" 2>/dev/null || true' EXIT
  supervise "$server"
}

case "${1:-}" in
  db) start_db ;;
  backend) start_backend ;;
  frontend) start_frontend ;;
  *)
    echo "usage: $0 db|backend|frontend" >&2
    exit 2
    ;;
esac
