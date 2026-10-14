# Frontend

React 19 app built with TanStack Start (server rendering + hydration), TanStack Router and Query, Tailwind CSS v4 and shadcn/ui. It talks to the backend over HTTP (`VITE_API_BASE_URL`, default `http://localhost:9095`).

## Run

```bash
bun install
bun run dev        # http://localhost:3000 (start the backend first, see ../README.md)
```

In Docker, the `frontend` service in `../docker-compose.yml` builds and serves the production bundle on port 3000.

## Scripts

| Script | What it does |
|---|---|
| `bun run dev` | Vite dev server on port 3000 |
| `bun run build` / `bun run preview` | Production build / preview it |
| `bun run test:e2e` (= `bun run test`) | Playwright end-to-end suite against the real backend and Postgres |
| `bun run lint` / `bun run lint:fix` | ESLint (app code and `e2e/`) |
| `bun run typecheck` | `tsc --noEmit` |
| `bun run format` / `bun run format:check` | Prettier |

The e2e suite needs Docker, uv, bun and Chromium (`bunx playwright install --with-deps chromium`). It uses its own ports (55432, 59095, 53000), so it can run next to the dev stack and `bun run dev`. The e2e frontend turns off the TanStack devtools event bus (fixed port 42069), so it shares no port.

## Pages

| Path | File | Notes |
|---|---|---|
| `/` | `src/routes/index.tsx` | Home |
| `/login`, `/register` | `src/routes/login.tsx`, `register.tsx` | `/login?redirect=<in-app path>` |
| `/items` | `src/routes/_authed/items.tsx` | Sign-in required (example CRUD feature) |
| `/oauth/callback`, `/oauth/error` | `src/routes/oauth/` | Google OAuth return pages |

## More

- Rules, patterns and folder layout: [AGENTS.md](AGENTS.md)
- How to write e2e tests: `../.claude/skills/project-standards/references/e2e-testing.md`
