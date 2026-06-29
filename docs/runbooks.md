# Runbooks

Operational runbooks for common incidents and maintenance tasks.

## Common Issues

### Backend Won't Start

**Symptom:** `docker compose up backend` fails or backend health check fails.

**Steps:**
1. Check database is running: `docker compose ps db`
2. Verify database connection: `docker compose exec db pg_isready -U app`
3. Check backend logs: `docker compose logs backend`
4. Verify environment variables in `.env` match `template/.env.example`
5. Run migrations manually: `cd template/backend && uv run alembic upgrade head`

### Database Migration Failure

**Symptom:** Alembic migration fails during backend startup.

**Steps:**
1. Check current migration version: `uv run alembic current`
2. View migration history: `uv run alembic history`
3. Rollback last migration: `uv run alembic downgrade -1`
4. Reset database: `docker compose down -v && docker compose up -d db && uv run alembic upgrade head`

### Frontend Build Errors

**Symptom:** `bun run build` fails with TypeScript or bundling errors.

**Steps:**
1. Clear node_modules: `rm -rf node_modules && bun install`
2. Check TypeScript: `bunx tsc --noEmit`
3. Check ESLint: `bun run lint`
4. Verify TanStack route tree is generated: check `src/routeTree.gen.ts` exists

### Dependency Pinning Issues

**Symptom:** Package installation fails due to version constraints.

**Steps:**
1. Check the supply-chain policy in AGENTS.md
2. Verify the package version is at least 7 days old
3. Check for open CVEs on the target version
4. Pin exactly with `==` (Python) or exact version (npm)

## Monitoring

- **Sentry:** Check error tracking dashboard for production errors
- **Axiom:** Check log ingestion for structured logs
- **Docker health checks:** Use `docker compose ps` to verify service health

## Escalation

For issues that cannot be resolved with these runbooks:
1. Check the [troubleshooting guide](./troubleshooting.md)
2. Review the [architecture documentation](./architecture.md)
3. Open an issue with the `bug` label
