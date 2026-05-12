# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

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

## Quick Reference

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

