# Frontend — Fullstack AI Template (Manta)

React 19 single-page application for the Manta fullstack template. Talks to the
FastAPI backend over a fetch-based API client with Bearer-token auth.

## Tech Stack

- **Framework:** React 19 + TypeScript
- **Routing:** TanStack Router (file-based in `src/routes/`), served via TanStack Start
- **Server State:** TanStack Query (React Query)
- **Styling:** Tailwind CSS v4 + shadcn/ui
- **Forms:** react-hook-form + Zod
- **Testing:** Vitest (unit) + Playwright (E2E)
- **Package Manager:** bun

## Getting Started

```bash
bun install
bun run dev          # Vite dev server on http://localhost:3000
```

The frontend expects the FastAPI backend to be running. By default it connects
to `http://localhost:9095` (see Configuration below).

## Available Scripts

| Command | Description |
| --- | --- |
| `bun run dev` | Start the Vite dev server (port 3000) |
| `bun run build` | Production build |
| `bun run preview` | Preview the production build |
| `bun run test` | Run unit tests (Vitest) |
| `bun run test:e2e` | Run E2E tests (Playwright) |
| `bun run lint` | Lint with ESLint |
| `bun run lint:fix` | Lint and auto-fix |
| `bun run format` | Format `src/` with Prettier |

## Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

| Variable | Description | Default |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Base URL of the FastAPI backend API | `http://localhost:9095` |

Configuration is read at runtime via `getConfig()` in `src/lib/config.ts`,
which validates the environment with Zod.

## Project Structure

```
src/
├── components/        React components (flat; shadcn/ui primitives in ui/)
├── contexts/          React Context providers (AuthContext)
├── features/          Feature-scoped modules
│   ├── auth/          Auth Zod schemas + submit orchestrator
│   └── items/         Item Zod schemas + payload helpers
├── hooks/             React hooks (useItems, useAuthSubmit, useDebounce, ...)
├── lib/               Generic infrastructure (api-client, config, error-handler, ...)
├── routes/            TanStack file-based routes
│   ├── __root.tsx     Root shell: providers, devtools, web-vitals
│   ├── index.tsx      Home page (/)
│   ├── items.tsx      Items list, auth-guarded (/items)
│   ├── login.tsx      Login (/login)
│   └── register.tsx   Register (/register)
├── styles/            Global CSS (app.css)
├── types/             Shared TypeScript types
└── test/              Test setup
```

## Routes

| Path | Description |
| --- | --- |
| `/` | Landing / home page |
| `/items` | Items list (requires auth; redirects to `/login` when unauthenticated) |
| `/login` | Login form |
| `/register` | Registration form |

Protected routes guard via `beforeLoad` checking `isAuthenticated()` from
`src/lib/auth.ts`.

## Data Flow

- **API client** (`src/lib/api-client.ts`): fetch wrapper that injects the
  Bearer token from localStorage, parses JSON errors into typed `ApiError`
  objects, and clears the token on 401.
- **Endpoints** (`src/lib/api-endpoints.ts`): the `API` endpoint registry and
  URL builders like `buildItemsListUrl()`.
- **Queries/Mutations** (`src/hooks/`): e.g. `useItems`, `useCreateItem`,
  `useUpdateItem`, `useDeleteItem` in `src/hooks/useItems.ts`.
- **Auth** (`src/contexts/AuthContext.tsx`): holds the session, exposes
  `login`/`logout`, and resets the React Query cache on logout.

React Query is constructed once in `src/routes/__root.tsx` and provided via
`QueryClientProvider` along with `AuthProvider`, `ErrorBoundary`, the `Layout`,
and the `Toaster`.

## Architecture Details

See [`FRONTEND_ARCHITECTURE.md`](./FRONTEND_ARCHITECTURE.md) for the full
architecture guide, and [`AGENTS.md`](./AGENTS.md) for development conventions.
