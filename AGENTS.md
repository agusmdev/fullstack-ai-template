# Agent Instructions

This repo is a **project generator**. `ai-fsr init <name>` (code in `ai_fsr/`) copies `template/` into a new project and applies a few substitutions. See [README.md](README.md).

## Project Structure

```
ai_fsr/                # Generator CLI: cli.py (Typer), init.py (copy, substitutions, IGNORED_NAMES)
template/              # The generated project. Its entry point for agents: template/AGENTS.md
├── AGENTS.md          # Start here for work inside the template
├── .claude/skills/project-standards/  # The master standards skill (SKILL.md + references/)
├── backend/           # FastAPI API server (see template/backend/AGENTS.md)
├── frontend/          # React 19 + TanStack Start app (see template/frontend/AGENTS.md)
├── docker-compose.yml # Services: db, backend, frontend
└── Makefile           # Dev commands (run `make help`)
.github/workflows/     # CI: backend-ci, frontend-ci (template), generator-ci (ai_fsr + smoke test)
```

- **Backend:** Python 3.12+, FastAPI, SQLAlchemy 2, Pydantic 2, Alembic, uv
- **Frontend:** React 19, TanStack Start/Router/Query, Tailwind v4, shadcn/ui, bun
- **Database:** PostgreSQL 18.1

## Standards

**Before writing or changing code in `template/`, read `template/.claude/skills/project-standards/SKILL.md` and follow it.** Then read `template/AGENTS.md` and the `AGENTS.md` of the part you change.

## Rules for this repo

- **Template changes must keep the template's own suites green.** Run `cd template && make ci` (static checks + backend e2e + Playwright e2e). Testing is end to end only: no mocks, no unit tests (see `template/AGENTS.md`).
- The generator replaces exact strings (`get_substitutions()` in `ai_fsr/init.py`) and fails if one is missing. When you change those lines in the template, change the generator too.
- When you add a local cache or build folder to the template, add it to `IGNORED_NAMES` in `ai_fsr/init.py` **and** to `[tool.hatch.build] exclude` in `pyproject.toml`.
- Generator checks: `uv run ruff check ai_fsr && uv run ruff format --check ai_fsr`, and a smoke run: `uv run ai-fsr init demo -o /tmp`.
- Docs: `AGENTS.md` is the only agent-instruction file. Do not add `CLAUDE.md` files.

## Supply-Chain Policy (npm + PyPI/uv)

**Before installing any third-party package**, the agent MUST follow this policy for both ecosystems.

### Step 1 — Web search
Look up the package's latest stable, non-vulnerable release. Check the registry page (npm or PyPI), the project's GitHub releases, and CVE advisories (GitHub Security Advisories, Snyk, `npm audit` / `pip-audit` / osv.dev).

### Step 2 — Verify
Confirm the chosen version is **at least 7 days old** and has no open critical/high CVEs. If the latest release is younger than 7 days, pick the most recent release that is ≥ 7 days old and note the choice in the commit message.

### Step 3 — Pin exactly

| Ecosystem | File | Pin format | Never |
|---|---|---|---|
| npm (bun/npm/pnpm) | `package.json` | `"foo": "1.2.3"` | `^1.2.3`, `~1.2.3`, `latest` |
| Python (uv) | `pyproject.toml` | `"foo==1.2.3"` (preserve extras: `"pydantic[email]==2.11.10"`) | `>=`, `~=`, `*` |

### Step 4 — Lock + commit
Run `bun install` / `npm install` (or `uv lock`) to regenerate the lockfile, then commit `package.json` + lockfile (or `pyproject.toml` + `uv.lock`) **together** so the resolved tree is locked in git.

The 7-day floor is also enforced globally for npm via `~/.npmrc` (`min-release-age=7`, `save-exact=true`) and `~/.bunfig.toml` (`minimumReleaseAge = 604800`). uv currently has no equivalent setting — the policy is the only enforcement, so do not skip step 2.

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

Push yourself instead of handing the push to the user, because unpushed work stays stranded locally. If the push fails, resolve the cause and push again.

