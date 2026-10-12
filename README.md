# ai-fsr — full-stack project generator

`ai-fsr` creates a new full-stack project from the `template/` folder of this repo:

- **Backend:** FastAPI, async SQLAlchemy 2, Alembic, Pydantic 2, uv (Python 3.12). Router → Service → Repository. Session auth + Google OAuth. Example `items` feature.
- **Frontend:** React 19, TanStack Start/Router/Query, Tailwind v4, shadcn/ui, bun.
- **Database:** PostgreSQL 18.1 in Docker Compose.
- **Tests:** end to end only — a backend API suite (real Postgres + live server) and a Playwright full-stack suite. Guards fail the run on mocks or untested routes.
- **For AI agents:** `AGENTS.md` files and one standards skill (`.claude/skills/project-standards/SKILL.md`).

## Create a project

Requirements: [uv](https://docs.astral.sh/uv/) and Docker (the command stops if `docker` is not on the PATH). To run the project you also need [bun](https://bun.sh/).

```bash
uvx --from git+https://github.com/agusmdev/fullstack-ai-template ai-fsr init my-app
```

From a local checkout of this repo (no `uv sync` needed first; `--directory` changes the working folder, so give `-o` an absolute path):

```bash
uv run --directory /path/to/fullstack-ai-template ai-fsr init my-app -o /path/to/parent
```

Then:

```bash
cd my-app
cp .env.example .env
docker compose up -d --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:9095 (no root page: `GET /` is 404; check http://localhost:9095/health or the docs at http://localhost:9095/docs)

**Next: open `my-app/AGENTS.md`.** It explains the project layout, the first-run steps, the testing rule and the Definition of Done. `my-app/README.md` is the human guide.

### Options

```
ai-fsr init PROJECT_NAME [OPTIONS]
```

| Option | What it does |
|---|---|
| `PROJECT_NAME` | Normalized to kebab-case (`My App` → `my-app`). `node`, `npm`, `test`, `package`, `frontend`, `backend` are reserved |
| `-o, --output-dir PATH` | Parent folder for the project (default: current folder) |
| `-f, --force` | Write into an existing folder: template files are overwritten, other files stay |
| `--dry-run` | Show what would be created, write nothing |
| `--git-init` | Run `git init` in the new project |
| `--install-deps` | Run `uv sync` in `backend/` and `bun install` in `frontend/` |

`ai-fsr --version` prints the version. Git hooks are not installed by `init`; after `git init`, run `make pre-commit-install` in the project.

### What the generator changes

With project name `N`, it copies `template/` and replaces:

| File | Change |
|---|---|
| `.env.example` | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` = `N` |
| `docker-compose.yml` | `${POSTGRES_*:-N}` defaults |
| `backend/.env.example` | `DB_URL=postgresql://N:N@localhost:5432/N` |
| `backend/pyproject.toml`, `backend/uv.lock` | `name = "N-backend"` |

Nothing else is renamed (Markdown and `frontend/package.json` stay as they are). Docker names the images `<folder>-backend` and `<folder>-frontend`.

The copy skips local junk (`node_modules`, `.venv`, caches, build output, test reports, `*.db`, `*.log`) and every `.env*` file except `.env.example` — see `IGNORED_NAMES` in `ai_fsr/init.py`.

## Work on the generator

```bash
git clone https://github.com/agusmdev/fullstack-ai-template
cd fullstack-ai-template
uv sync                          # installs ai-fsr (editable) and ruff
uv run ai-fsr init demo -o /tmp  # try it
uv run ruff check ai_fsr && uv run ruff format ai_fsr
```

| Path | What it is |
|---|---|
| `ai_fsr/cli.py` | Typer CLI (`ai-fsr init`) |
| `ai_fsr/init.py` | Copy, substitutions (`get_substitutions`), copy filter (`IGNORED_NAMES`), post-init steps |
| `template/` | The project that gets copied. Its own docs start at `template/AGENTS.md` |
| `.github/workflows/` | CI for this repo: `backend-ci.yml`, `frontend-ci.yml` (template lint + both e2e suites), `generator-ci.yml` (ruff on `ai_fsr`, a generated-project smoke test) |
| `pyproject.toml` | Package config. `[tool.hatch.build] exclude` keeps junk out of the wheel; keep it in sync with `IGNORED_NAMES` |
| `AGENTS.md` | Rules for agents working on this repo |

Rules for template changes:

- The generator fails if a placeholder in the table above is missing. If you change those lines in the template, update `get_substitutions()` too.
- The template's own checks must stay green: `cd template && make ci` (static checks + both e2e suites).
- The wheel ships the template as `ai_fsr/template`. Only the repo-root `.gitignore` and the `[tool.hatch.build] exclude` list filter it; the nested `template/*/.gitignore` files do not.
