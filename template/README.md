# Linear Clone — Template Showcase App

A real, production-grade **Linear clone** built directly inside this fullstack
template. It replaces the starter `items` example and demonstrates that the
template can produce a fast, polished, complex product: issues, projects,
cycles, board/list views, teams, labels, statuses, priorities, sub-issues,
dependencies, comments, an activity log, a Cmd+K command palette, keyboard
shortcuts, and dark mode — with Linear-like speed (optimistic updates +
short-interval polling, no websockets).

This is the **showcase application** for the template. The backend and frontend
below *are* the Linear app; the generic `items` example has been removed.

## Features

- **Teams & roles** — multi-team workspace with admin/member/guest roles;
  every entity is team-scoped so users only see data for teams they belong to.
  A default team is auto-created on registration.
- **Issues** — the core entity. Auto-generated per-team identifiers (`TEAM-123`),
  statuses (workflow states), priorities (Urgent→No priority), assignees,
  labels, projects, cycles, estimates, due dates. Full CRUD with server-side
  filter / search / sort / pagination.
- **Workflow states** — five canonical states per team (Backlog, Todo, In
  Progress, Done, Canceled) ordered by position.
- **Projects** — group related issues; track status, lead, and target date.
- **Cycles** — time-boxed sprints with start/end windows and progress tracking.
- **Board** — a kanban view, one column per workflow status, with drag-and-drop
  status changes (optimistic + persisted, with rollback on failure).
- **Views** — save a filter/group-by/sort configuration and return to it.
- **Sub-issues** — nest issues under a parent (self-reference), with expand/
  collapse and aggregate progress.
- **Dependencies** — mark "A blocks B"; reciprocal display; circular-dependency
  guard.
- **Comments** — threaded, newest-first, author-scoped edit/delete.
- **Activity** — auto-generated, read-only feed of every issue change (status,
  priority, assignee, title, labels).
- **Command palette** — Cmd+K / Ctrl+K fuzzy search over navigation targets and
  quick actions.
- **Keyboard shortcuts** — `c` create issue, `g i` go to issues, `[` / `]`
  navigate prev/next issue, `Esc` close, `?` shortcuts help.
- **Dark mode** — light/dark/system, applied before first paint, persisted in
  localStorage across reload and logout/login.
- **Performance** — optimistic updates everywhere, stale-while-revalidate,
  short-interval polling, indexed queries, skeleton loaders, and empty states
  on every async surface.

## Tech Stack

| Layer      | Technology                                                            |
| ---------- | -------------------------------------------------------------------- |
| Frontend   | React 19, TanStack Router + React Query, Tailwind v4, shadcn/ui, Zod |
| Backend    | FastAPI, async SQLAlchemy 2, Pydantic 2, Alembic, fastapi_filter/pagination |
| Database   | PostgreSQL 18.1 (asyncpg)                                            |
| Auth       | Session/Bearer (argon2), team-scoped authorization                   |
| Tooling    | uv (Python), bun (JS), ruff, eslint, vitest, pytest                 |

## Quick Start

### Prerequisites

- Docker + Docker Compose
- [uv](https://docs.astral.sh/uv/) (Python)
- [bun](https://bun.sh/) (JavaScript)

### 1. Start the database

```bash
docker compose up -d db          # Postgres 18.1 on host port 5433
```

> The showcase uses host port **5433** (set `DB_PORT=5433`) to avoid clashes
> with any existing local Postgres on 5432.

### 2. Run the backend

```bash
cd backend
cp .env.example .env             # then edit DB_URL / DB_PORT as needed
uv sync
uv run alembic upgrade head      # apply migrations
# The app uses a factory — invoke with --factory:
DB_PORT=5433 uv run uvicorn --factory app.main:create_app --port 9095
```

The API is served at `http://localhost:9095` (OpenAPI docs at `/docs`).

### 3. Run the frontend

```bash
cd frontend
bun install
bun run dev                     # Vite dev server on http://localhost:3000
```

Open `http://localhost:3000`, register an account, and you'll land in your
team workspace with a default team and the canonical workflow states ready.

### Default ports

| Service   | Port |
| --------- | ---- |
| Frontend  | 3000 |
| Backend   | 9095 |
| Postgres  | 5433 |

## Project Structure

```
template/
├── backend/
│   ├── app/
│   │   ├── modules/            # Linear domain modules (3-layer each)
│   │   │   ├── teams/          # Team, TeamMembership (roles)
│   │   │   ├── workflows/      # WorkflowState (statuses)
│   │   │   ├── labels/         # Label + IssueLabel (M2M)
│   │   │   ├── issues/         # Issue — the core entity (hub)
│   │   │   ├── projects/       # Project
│   │   │   ├── cycles/         # Cycle (sprints)
│   │   │   ├── views/          # Saved View
│   │   │   ├── comments/       # Comment
│   │   │   └── activity/       # Activity (auto-generated, read-only)
│   │   ├── user/               # User + auth (register/login/logout/me)
│   │   ├── routers.py          # Central router registration
│   │   └── main.py             # App factory (create_app)
│   ├── tests/                  # pytest (unit + integration)
│   └── alembic/                # Migrations
├── frontend/
│   ├── src/
│   │   ├── routes/             # TanStack file-based routes
│   │   │   ├── __root.tsx      # Shell + providers + toaster
│   │   │   ├── login.tsx, register.tsx
│   │   │   ├── _authed.tsx     # Auth guard + workspace shell
│   │   │   └── _authed/$team/  # Team-scoped workspace (issues, board,
│   │   │       #   projects, cycles, views, settings, detail routes)
│   │   ├── components/         # Sidebar, Topbar, IssueList/Board/Drawer,
│   │   │                       # pickers, dialogs, palette, skeletons…
│   │   ├── hooks/              # useIssues, useProjects, useCycles, …
│   │   │                       # (optimistic mutations + polling)
│   │   ├── contexts/           # CommandPalette, KeyboardShortcuts
│   │   ├── lib/                # api-client, endpoints, theme, query-keys
│   │   └── types/              # TypeScript domain types
│   └── tests / *.test.tsx      # Vitest + React Testing Library (co-located)
└── docker-compose.yml          # Postgres service
```

## Architecture

**Backend** keeps the template's strict 3-layer pattern
(`Router → Service → Repository`) with generic CRUD (`BaseService[T]` +
`SQLAlchemyRepository[T]`), `fastapi_filter` + `fastapi_pagination`, and
session/Bearer auth (argon2). Every router is guarded by
`require_current_user_id`; every service scopes queries by team membership and
enforces role-based access (`require_team_access`).

The **Issue** is the hub of the data model: it references team, workflow state,
assignee, creator, project, cycle, and an optional parent (sub-issues).
Identifiers (`TEAM-123`) are generated from a per-team counter. Hot columns
(`team_id`, `status_id`, `assignee_id`, `project_id`, `cycle_id`, `parent_id`,
`team_id + identifier`) are indexed, and labels are eager-loaded (`selectin`)
to avoid N+1 on list/board queries.

**Frontend** uses TanStack Router (file-based), React Query, and shadcn/ui.
Mutations use **optimistic updates** (`onMutate` cache patch + `onError`
rollback + `onSettled` invalidate) for instant UI feedback. Active views poll
on a short interval (stale-while-revalidate) for near-real-time freshness
without websockets.

## Development Commands

### Backend (run from `backend/`)

```bash
uv run pytest tests/ -q                 # run tests
uv run ruff check app --fix && uv run ruff format app   # lint + format
uv run alembic revision --autogenerate -m "description" # create migration
uv run alembic upgrade head             # apply migrations
```

### Frontend (run from `frontend/`)

```bash
bun run test      # vitest
bun run lint      # eslint
bunx tsc --noEmit # typecheck
bun run dev       # dev server
bun run build     # production build
```

## API Overview

All endpoints are under the backend root (e.g. `http://localhost:9095`) and
require a `Authorization: Bearer <token>` header (obtained via `/auth/register`
or `/auth/login`), except the auth endpoints themselves.

| Method | Path                         | Description                          |
| ------ | ---------------------------- | ------------------------------------ |
| POST   | `/auth/register`             | Register, returns token + session    |
| POST   | `/auth/login`                | Login, returns token + session       |
| POST   | `/auth/logout`               | Invalidate session                   |
| GET    | `/users/me`                  | Current user                         |
| GET    | `/teams`                     | Teams the user belongs to            |
| GET    | `/workflow-states`           | Team workflow states                 |
| GET    | `/issues`                    | Issues (filter/sort/paginate)        |
| POST   | `/issues`                    | Create issue                         |
| GET    | `/issues/{id}`               | Issue detail                         |
| PATCH  | `/issues/{id}`               | Update issue                         |
| DELETE | `/issues/{id}`               | Delete issue                         |
| GET/POST/PATCH/DELETE | `/projects`, `/cycles`, `/views`, `/comments` | CRUD for each |
| GET    | `/activity?issue_id=`        | Activity feed for an issue           |

Interactive docs are available at `http://localhost:9095/docs` (Swagger) and
`/redoc` once the backend is running.

## Testing

- **Backend:** `uv run pytest tests/ -q` — unit tests (mocked repo/service)
  plus integration tests.
- **Frontend:** `bun run test` — co-located Vitest + React Testing Library
  tests for components, hooks, and routes.
- **End-to-end:** the app is verified by driving the real SPA against the real
  FastAPI + Postgres (no mocks) through a browser automation harness.

## License

MIT
