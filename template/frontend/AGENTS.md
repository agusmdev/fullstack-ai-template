# AGENTS.md - Frontend Development Guide

## Quick Commands
- **Install:** `bun install`
- **Dev:** `bun run dev` (port 3000)
- **Build:** `bun run build`
- **Test:** `bun run test` (vitest)
- **E2E:** `bun run test:e2e` (playwright)
- **Lint:** `bun run lint`
- **Lint fix:** `bun run lint:fix`
- **Format:** `bun run format`

## Tech Stack
- **Framework:** React 19 with TypeScript
- **Router:** TanStack Router (file-based in `src/routes/`)
- **State:** React Query for server state
- **Styling:** Tailwind CSS v4
- **UI:** shadcn/ui components (`src/components/ui/`)
- **Forms:** react-hook-form + Zod validation
- **Testing:** Vitest (unit), Playwright (E2E)
- **Package Manager:** bun (all commands use `bun run`)

## Configuration
- **Dev Port:** 3000 (Vite dev server)
- **API Base:** `VITE_API_BASE_URL` (default: `http://localhost:9095`)
- **Imports:** Use `@/` path alias (maps to `src/`)

## Folder Structure
```
src/
├── components/
│   ├── ui/              ← shadcn/ui components ONLY
│   ├── Navigation.tsx   ← Top nav bar
│   ├── Layout.tsx       ← Page layout wrapper
│   ├── ErrorBoundary.tsx
│   ├── CreateItemDialog.tsx
│   ├── EditItemDialog.tsx
│   └── DeleteItemDialog.tsx
├── contexts/            ← React Context (AuthContext, etc.)
├── hooks/               ← All hooks flat (useItems.ts, useDebounce.ts, etc.)
├── lib/
│   ├── api-client.ts    ← Fetch wrapper with auth & error handling
│   ├── api-endpoints.ts ← Endpoint URL constants
│   ├── auth.ts          ← Token storage/retrieval + pub-sub
│   ├── query-keys.ts    ← Query key factory
│   ├── config.ts        ← Runtime configuration
│   ├── error-handler.ts ← Error handling utilities
│   ├── schemas.ts       ← Zod validation schemas
│   └── utils.ts         ← Helper utilities
├── routes/              ← TanStack file-based routes
│   └── __root.tsx       ← Root layout with providers
├── types/               ← TypeScript types & interfaces
├── styles/              ← Global CSS
└── test/                ← Testing utilities & setup
```

## API Layer Pattern

**Endpoints** (`lib/api-endpoints.ts`):
```tsx
export const API = {
  AUTH: {
    REGISTER: '/auth/register',
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
  },
  ITEMS: {
    LIST: '/items',
    CREATE: '/items',
    DETAIL: (id: string) => `/items/${id}`,  // used for GET, PATCH, DELETE
  },
} as const
```

**API Client** (`lib/api-client.ts`):
- Automatic Bearer token injection
- 401: clears token and throws ApiError; `AuthContext` handles redirect to `/login` via `subscribeToAuthChanges`
- JSON error parsing with detail/code/fields
- Throws `ApiError` with typed properties

## Query & Mutation Patterns

All item queries and mutations live in `hooks/useItems.ts` as individual exported hooks:

```tsx
// Query
export function useItems(params?: ItemsParams, enabled = true) {
  return useQuery({
    queryKey: queryKeys.items.list(params),
    queryFn: () => api.get<ItemsResponse>(API.ITEMS.LIST + buildQuery(params)),
    enabled,
  })
}

// Mutation
export function useCreateItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateItemData) => api.post<Item>(API.ITEMS.CREATE, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.items.all }),
  })
}
```

## Form Pattern

**Schema-first** with Zod and react-hook-form:
```tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const itemSchema = z.object({
  name: z.string().min(1, 'Name required'),
  description: z.string().optional(),
})

const form = useForm({
  resolver: zodResolver(itemSchema),
  defaultValues: { name: '', description: '' },
})
```

## Auth Pattern

**Protected Routes:**
- Check `useAuth().isAuthenticated` in components
- Loaders can validate auth before rendering
- Failed auth redirects to `/login` (automatic via api-client)

**Token Storage:**
- localStorage via `lib/auth.ts` functions
- No auth token = anonymous user
- Logout clears token + invalidates queries

## Error Handling

**API Errors:**
- `ApiError` with `status`, `code`, `fields` properties
- Network/400s: use `error.detail` for messages
- Validation errors: use `error.fields` for form feedback
- 401 errors: auto-redirect to `/login`

**User Feedback:**
- Toast notifications via `sonner` (already imported in `__root.tsx`)
- Example: `toast.error(error.detail)`

## Testing

**Unit Tests** (Vitest + React Testing Library):
```tsx
import { render, screen } from '@testing-library/react'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'

// Wrap components with QueryClientProvider
const queryClient = new QueryClient()
render(
  <QueryClientProvider client={queryClient}>
    <YourComponent />
  </QueryClientProvider>
)
```

**E2E Tests** (Playwright):
- Located in `e2e/` directory
- Run with `bun run test:e2e`

## Naming Conventions

**Files:**
- Hooks: `use*.ts` flat in `hooks/` (useItems.ts, useDebounce.ts)
- Components: `components/*.tsx` flat (CreateItemDialog.tsx, Navigation.tsx)
- Types: `types/*.ts` (no `.d.ts` for imports)
- Utilities: `lib/*.ts` with named exports

**Components:**
- All components flat in `components/` (no subdirectories)
- Dialog components: `*Dialog` suffix
- Layout/shared components: alongside feature components

**Query Keys:**
- First level: feature name (items, users, etc.)
- Subsequent levels: operation (list, detail, search)
- Always include params in key for caching

**Exports:**
- Named exports for utilities, types, components
- Default export for route components only

## Git & Commits

- **Conventional Commits:** `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- **Examples:**
  - `feat: add item creation dialog`
  - `fix: handle 401 errors in api client`
  - `refactor: extract form validation to hook`

## Workflow

See root `AGENTS.md` for "Landing the Plane" workflow:
1. Run `bun run test` and `bun run lint:fix`
2. Commit changes with conventional commits
3. `git push` to origin
4. Verify with `git status`
