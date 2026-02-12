# Agent Instructions

## Project Structure

```
template/
├── backend/           # FastAPI API server (see backend/AGENTS.md)
├── frontend/          # React 19 SPA (see frontend/AGENTS.md)
├── docker-compose.yml # Service orchestration (db, backend, frontend)
└── Makefile           # Dev commands (run `make help`)
```

- **Backend:** Python 3.12+, FastAPI, SQLAlchemy 2, Pydantic 2, Alembic, uv
- **Frontend:** React 19, TanStack Router/Query, Tailwind v4, shadcn/ui, bun
- **Database:** PostgreSQL 18.1

**Skills for common tasks:**
- `/skill:add-backend-entity` — Add a new API resource to the backend
- `/skill:add-frontend-feature` — Add a new UI feature to the frontend
- `/skill:backend-filters` — Filter/pagination system reference
- `/skill:backend-logging` — Structured logging system reference

## Issue Tracking

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

