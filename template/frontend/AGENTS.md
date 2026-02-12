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
│   ├── common/          ← Shared features (Navigation, Layout, ErrorBoundary)
│   └── {feature}/       ← Feature-scoped (items/, auth/)
│       └── dialogs/     ← Feature dialogs
├── contexts/            ← React Context (AuthContext, etc.)
├── hooks/
│   ├── queries/         ← queryOptions factories (useItemsQuery, etc.)
│   ├── mutations/       ← useMutation hooks (useCreateItem, etc.)
│   └── use*.ts          ← Other hooks (useAuth, useErrorHandler, etc.)
├── lib/
│   ├── api-client.ts    ← Fetch wrapper with auth & error handling
│   ├── api-endpoints.ts ← Endpoint URLs constant
│   ├── auth.ts          ← Token storage/retrieval
│   ├── query-keys.ts    ← Query key factory
│   ├── config.ts        ← Runtime configuration
│   ├── error-handler.ts ← Error handling utilities
│   ├── schemas/         ← Zod validation schemas
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
    REGISTER: '/api/v1/auth/register',
    LOGIN: '/api/v1/auth/login',
    LOGOUT: '/api/v1/auth/logout',
    ME: '/api/v1/auth/me',
  },
  ITEMS: {
    LIST: '/api/v1/items',
    CREATE: '/api/v1/items',
    DETAIL: (id: string) => `/api/v1/items/${id}`,
    UPDATE: (id: string) => `/api/v1/items/${id}`,
    DELETE: (id: string) => `/api/v1/items/${id}`,
  },
} as const
```

**API Client** (`lib/api-client.ts`):
- Automatic Bearer token injection
- 401 redirect to `/login`
- JSON error parsing with detail/code/fields
- Throws `ApiError` with typed properties

## Query & Mutation Patterns

**Query with queryOptions** (`hooks/queries/use*.ts`):
```tsx
import { queryOptions } from '@tanstack/react-query'

export const itemsQueryOptions = () =>
  queryOptions({
    queryKey: ['items', 'list'],
    queryFn: () => api.get(API.ITEMS.LIST),
    staleTime: 1000 * 60 * 5,
  })

// Usage: const { data } = useQuery(itemsQueryOptions())
```

**Mutation with invalidation** (`hooks/mutations/use*.ts`):
```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query'

export function useCreateItem() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: ItemCreate) => api.post(API.ITEMS.CREATE, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['items'] })
    },
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
- Hooks: `use*.ts` (useAuth, useItems)
- Query hooks: `hooks/queries/use*Query.ts`
- Mutation hooks: `hooks/mutations/use*Mutation.ts`
- Components: `components/{Feature}/{ComponentName}.tsx`
- Types: `types/*.ts` (no `.d.ts` for imports)
- Utilities: `lib/*.ts` with named exports

**Components:**
- Feature folders: singular (items/, auth/, not items/, auths/)
- Feature components: `ItemsList`, `ItemCard`, `ItemForm`
- Dialog components: `*Dialog` suffix
- Layout components: in `components/common/`

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
