# AGENTS.md — start here

Full-stack web app: a FastAPI backend, a React 19 frontend (TanStack Start) and PostgreSQL 18.1, run together with Docker Compose. Session auth (register, login, OAuth with Google) and an example `items` feature are included.

## Rule 0: read the standards first

**Before writing or changing code, read `.claude/skills/project-standards/SKILL.md` and follow it.**

The path is relative to the project root (the folder of this file). It is a plain Markdown file: any agent or person can open it. The files in `.claude/skills/project-standards/references/` give the details for each topic.

Then read the `AGENTS.md` of the part you change:

- [backend/AGENTS.md](backend/AGENTS.md) — FastAPI, SQLAlchemy, Alembic, uv
- [frontend/AGENTS.md](frontend/AGENTS.md) — React 19, TanStack Start/Router/Query, Tailwind v4, shadcn/ui, bun

## Prerequisites

| Tool | Used for |
|---|---|
| Docker with Compose v2 | the dev stack and both test suites |
| [uv](https://docs.astral.sh/uv/) | backend outside Docker, backend tests, git hooks |
| [bun](https://bun.sh/) | frontend outside Docker, frontend tests |
| git | version control and the pre-commit hooks |

## First run (Docker)

```bash
cp .env.example .env          # optional: every value has a default in docker-compose.yml
docker compose up -d --build  # `make start` = `docker compose up -d` (no rebuild)
```

The backend container runs `alembic upgrade head` before it starts.

| URL | What |
|---|---|
| http://localhost:3000 | Frontend |
| http://localhost:9095 | Backend API (no `/api` prefix; no root route, so `GET /` is 404: use `/health` or `/docs` to check it) |
| http://localhost:9095/docs | OpenAPI docs |
| http://localhost:9095/health | Health check |

Stop: `docker compose down`. Reset the database: `make db-reset` (deletes the data; afterwards only `db` runs, so run `docker compose up -d` to start the backend and frontend again). Ports clash? Change `BACKEND_PORT`, `FRONTEND_PORT` or `DB_PORT` in `.env`. The URLs in `.env` do not follow the ports: with a new `BACKEND_PORT` also change `VITE_API_BASE_URL` (and `GOOGLE_REDIRECT_URI` if you set it); with a new `FRONTEND_PORT` also change `FRONTEND_URL`. Then run `docker compose up -d --build` (the frontend bakes `VITE_API_BASE_URL` in at build time). See [README.md](README.md#environment).

## Run backend and frontend outside Docker (hot reload)

```bash
docker compose up -d db                       # Postgres only

cd backend
cp .env.example .env                          # DB_URL must match POSTGRES_* in the root .env
uv sync
uv run alembic upgrade head
make run                                      # http://localhost:9095, reload on save

cd ../frontend                                # in a second terminal
bun install
bun run dev                                   # http://localhost:3000
```

## Git hooks (once, after `git init`)

```bash
(cd backend && uv sync) && (cd frontend && bun install)
make pre-commit-install       # ruff, frontend eslint + prettier, no-mock guards
```

## File map

| Path | What it is |
|---|---|
| `AGENTS.md` | This file: the entry point for agents |
| `README.md` | Human getting-started guide, environment variables, make targets |
| `.claude/skills/project-standards/` | The project standards (`SKILL.md` + `references/`). Mandatory reading |
| `.env.example` | Template for the root `.env`. Docker Compose reads `.env` |
| `.gitignore` | Ignores `.env` files (not `.env.example`), editor and OS files |
| `.pre-commit-config.yaml` | The one git-hook config for the whole project |
| `docker-compose.yml` | Services `db`, `backend`, `frontend` with their env and healthchecks |
| `Makefile` | All dev commands. Run `make help` |
| `backend/` | FastAPI API server |
| `backend/app/` | App code: `main.py` (app factory), `routers.py`, `core/`, `database/`, `repositories/`, `services/`, `dependencies/`, `integrations/`, `user/` (users + auth), `modules/` (features, e.g. `items/`) |
| `backend/app/migrations/` | Alembic migrations (`env.py` + `versions/`) |
| `backend/tests/e2e/` | Backend end-to-end suite (live server + real Postgres) |
| `backend/.env.example` | Backend settings for runs **outside** Docker only |
| `backend/pyproject.toml`, `backend/uv.lock` | Python dependencies (exact pins), ruff and pytest config |
| `backend/Dockerfile`, `backend/alembic.ini`, `backend/Makefile` | Image build, Alembic config, backend-only commands |
| `frontend/` | React app |
| `frontend/src/` | `routes/` (file-based pages; `_authed/` = sign-in required), `components/` (`ui/` = shadcn), `hooks/`, `lib/` (API client, endpoints, auth), `features/`, `contexts/`, `types/`, `styles/` |
| `frontend/e2e/` | Playwright full-stack suite (`fixtures.ts`, `*.spec.ts`, `guards.spec.ts`, `support/`) |
| `frontend/public/` | Static files (`favicon.ico`, `robots.txt`) |
| `frontend/package.json`, `frontend/bun.lock` | npm dependencies (exact pins), scripts, lint-staged config |
| `frontend/playwright.config.ts`, `frontend/eslint.config.js`, `frontend/vite.config.ts` | Test stack, lint rules (incl. no-mock rules), build |

## Testing: end-to-end only

There are **no unit tests, no mocks, no fakes, no dependency overrides and no network interception**. Every test drives the real system:

- **Backend:** real Postgres (testcontainers) → real `alembic upgrade head` + `alembic check` → real `uvicorn` → tests send HTTP. Tests go in `backend/tests/e2e/test_<feature>.py`.
- **Frontend:** Playwright → real Vite dev server → real backend → real Postgres. Tests go in `frontend/e2e/<feature>.spec.ts`.

Guards fail the run when someone adds a mock, a test outside the e2e folders, a backend route with no successful e2e request, a page or API endpoint that no spec uses, or a model change with no migration.

How to write a test, fixtures and guards: `.claude/skills/project-standards/references/e2e-testing.md`.

| Command (project root) | What it runs |
|---|---|
| `make test` | Both suites: backend, then full stack |
| `make test-backend` | Backend suite (`cd backend && uv run pytest`). Needs Docker |
| `make test-backend-cov` | Backend suite with coverage (`backend/htmlcov/`) |
| `make test-e2e` | Full-stack suite (`cd frontend && bun run test:e2e`). Needs Docker, uv, bun, Chromium (`cd frontend && bunx playwright install --with-deps chromium`) |
| `make check` | Every static check, no file changes: ruff, ESLint, prettier, `tsc`, build |
| `make ci` | `make check` + `make test` |

The test suites use their own ports (Postgres 55432, backend 59095, frontend 53000) and never touch the dev stack. The e2e frontend turns off the TanStack devtools event bus (fixed port 42069), so `bun run dev` can stay up.

## Definition of Done

A change is done only when all items are true:

1. The code follows `.claude/skills/project-standards/SKILL.md`.
2. Every new or changed backend endpoint has an e2e test in `backend/tests/e2e/` with at least one successful request.
3. Every new or changed page, and every new entry in `frontend/src/lib/api-endpoints.ts`, is used by a spec in `frontend/e2e/`.
4. A model change has an Alembic migration (run `make migrate` first, then `make migrate-create message="..."`; it needs `backend/.env` and an up-to-date database, and the new file needs `make format && make lint-fix`). See `.claude/skills/project-standards/references/backend-entity.md` step 11.
5. `make check` passes.
6. `make test` passes.
7. New third-party packages follow the supply-chain rule below.
8. When a command, path or rule changes, the `AGENTS.md` files and `README.md` say so.

## Supply-chain rule (npm and PyPI)

Before you add a package: use a release that is **at least 7 days old** and has no open critical/high CVE. Pin it exactly (`"foo": "1.2.3"` in `package.json`, `"foo==1.2.3"` in `pyproject.toml`). Commit the manifest together with the lockfile (`bun.lock` or `uv.lock`).
