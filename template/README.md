# Full-Stack App

FastAPI backend + React 19 frontend (TanStack Start) + PostgreSQL 18.1, run with Docker Compose.

| Part | Stack | Docs |
|---|---|---|
| `backend/` | Python 3.12, FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic 2, uv | [backend/AGENTS.md](backend/AGENTS.md) |
| `frontend/` | React 19, TanStack Start/Router/Query, Tailwind v4, shadcn/ui, bun | [frontend/AGENTS.md](frontend/AGENTS.md) |
| `db` | PostgreSQL 18.1 (`postgres:18.1-alpine`) | `docker-compose.yml` |

Included: session auth (register, login, logout, password reset, email verification, Google OAuth), an example `items` CRUD feature, structured request logging, and two end-to-end test suites.

**Working with an AI agent?** It starts at [AGENTS.md](AGENTS.md). Code standards for agents and people: `.claude/skills/project-standards/SKILL.md`.

## 1. Prerequisites

- Docker with Compose v2
- [uv](https://docs.astral.sh/uv/) — backend outside Docker, backend tests, git hooks
- [bun](https://bun.sh/) — frontend outside Docker, frontend tests

## 2. Start everything with Docker

```bash
cp .env.example .env          # optional; every value has a default
docker compose up -d --build  # `make start` = `docker compose up -d` (no rebuild)
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:9095 (no `/api` prefix; `GET /` is 404, check `/health`)
- API docs: http://localhost:9095/docs

The backend container runs the migrations (`alembic upgrade head`) before it starts. Logs: `make logs`. Stop: `make down`. Reset the database: `make db-reset`, then `docker compose up -d` (the reset leaves only `db` running).

## 3. Develop with hot reload (optional)

Run Postgres in Docker and the apps on your machine:

```bash
docker compose up -d db

# terminal 1
cd backend
cp .env.example .env          # DB_URL must match POSTGRES_* in the root .env
uv sync && uv run alembic upgrade head
make run                      # http://localhost:9095

# terminal 2
cd frontend
bun install && bun run dev    # http://localhost:3000
```

`make setup` copies both `.env` files and installs the backend and frontend dependencies in one step.

## 4. Git hooks

After `git init` (and `uv sync` in `backend/`, `bun install` in `frontend/`):

```bash
make pre-commit-install       # ruff, frontend eslint + prettier, no-mock guards
make pre-commit-run           # run them on every tracked file
```

The hooks are in `.pre-commit-config.yaml`. They are fast early warnings; the real checks are `make check` and `make test`.

## Environment

There are two sets of settings:

| File | Read by | Used for |
|---|---|---|
| `.env` (from `.env.example`) | Docker Compose | Ports, Postgres credentials, every backend setting for the container, the frontend build URL |
| `backend/.env` (from `backend/.env.example`) | the backend when you run it **outside** Docker (`make run`) | Same backend settings; `DB_URL` points at `localhost` |
| `frontend/.env` (from `frontend/.env.example`, optional) | `bun run dev` / `bun run build` outside Docker | `VITE_API_BASE_URL` |

Docker Compose does **not** read `backend/.env`. The backend container gets its settings only from `docker-compose.yml`, which takes them from the root `.env` (with defaults). All `.env` files are git-ignored; the `.env.example` files are committed.

### Root `.env` variables

| Variable | Default | Notes |
|---|---|---|
| `BACKEND_PORT`, `FRONTEND_PORT`, `DB_PORT` | `9095`, `3000`, `5432` | Host ports. Check what is free: `make check-ports` |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | the project name (`app` in the raw template; `ai-fsr init` sets them) | Used by `db`, and to build the backend `DB_URL` (host `db`) |
| `DB_URL` | built from `POSTGRES_*` | Not in `.env.example`. Set it only for an external Postgres, or when the password has `@ : / # %` (URL-encode them) |
| `DB_POOL_SIZE`, `DB_POOL_PRE_PING` | `100`, `false` | SQLAlchemy pool |
| `APP_NAME`, `ENVIRONMENT`, `DEBUG_MODE` | `backend`, `local`, `false` | Sentry is off when `ENVIRONMENT=local` |
| `LOG_LEVEL`, `LOG_FORMAT` | `INFO`, `console` | `json` = one wide event per request, for log shipping |
| `FRONTEND_URL` | `http://localhost:3000` | CORS origin and OAuth redirect target. Keep in sync with `FRONTEND_PORT` |
| `SENTRY_DSN`, `SENTRY_TRACES_SAMPLE_RATE`, `SENTRY_PROFILES_SAMPLE_RATE` | empty, `0.0`, `0.0` | Empty DSN = off |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | empty | Empty = Google OAuth not set up |
| `GOOGLE_REDIRECT_URI` | `http://localhost:${BACKEND_PORT}/auth/oauth/google/callback` | Must match the Google console |
| `VERSION`, `COMMIT_HASH`, `INSTANCE_ID` | empty | Optional log context |
| `VITE_API_BASE_URL` | `http://localhost:9095` | Baked into the frontend image at build time |

### Change a port

Set the new port in `.env`. For the backend port, also change `VITE_API_BASE_URL` (and `GOOGLE_REDIRECT_URI` if you set it); for the frontend port, also change `FRONTEND_URL`. Then rebuild: `docker compose up -d --build`.

### Change the database credentials

Change `POSTGRES_*` in `.env` and the matching `DB_URL` in `backend/.env`. An existing database volume keeps the old credentials: reset it with `make db-reset` (this deletes the data), then run `docker compose up -d` (the reset starts only `db`).

## Tests

All tests are end to end against the real stack. There are no unit tests and no mocks.

```bash
make test             # both suites
make test-backend     # API suite: Postgres (testcontainers) + migrations + live server (needs Docker)
make test-e2e         # browser suite: Postgres + backend + Vite + Playwright (needs Docker, uv, bun, Chromium)
make check            # every static check: ruff, ESLint, prettier, tsc, build
make ci               # check + test
```

First Playwright run: `cd frontend && bunx playwright install --with-deps chromium`. The suites use their own ports (55432, 59095, 53000) and never touch the dev stack. The e2e frontend turns off the TanStack devtools event bus (fixed port 42069), so `bun run dev` can stay up.

Where tests go and how to write them: [AGENTS.md](AGENTS.md#testing-end-to-end-only) and `.claude/skills/project-standards/references/e2e-testing.md`.

## Make targets

Run `make help` for the full list. The most used:

| Target | What it does |
|---|---|
| `make start` / `make down` | Start the stack in the background / stop it |
| `make logs`, `make logs-backend` | Follow logs |
| `make rebuild` | Rebuild images and start |
| `make migrate`, `make migrate-create message="..."`, `make migrate-rollback` | Alembic |
| `make db-shell`, `make db-reset` | psql in the `db` container / wipe and re-migrate (only `db` runs afterwards; then `docker compose up -d`) |
| `make lint`, `make lint-fix`, `make format`, `make typecheck` | Code quality (both apps) |
| `make backend-typecheck` | ty on the backend (advisory, not in CI) |
| `make clean` | Remove this project's containers, networks and volumes |

## Troubleshooting

| Problem | Fix |
|---|---|
| Port already in use | `make check-ports`, then change the port in `.env` (see above) |
| Backend cannot reach the database | `docker compose ps`, `make logs-db`; after a credential change run `make db-reset`, then `docker compose up -d` |
| Frontend calls the wrong backend URL | `VITE_API_BASE_URL` is baked in at build time: `docker compose up -d --build frontend` |
| `make test-e2e` says a port is busy | Another e2e run uses it. Wait, or set `E2E_DB_PORT`, `E2E_BACKEND_PORT`, `E2E_FRONTEND_PORT` |
| `bun run dev` fails with `EADDRINUSE ... 42069` | Another `bun run dev` holds the TanStack devtools port. Stop it (e2e runs do not use 42069) |
