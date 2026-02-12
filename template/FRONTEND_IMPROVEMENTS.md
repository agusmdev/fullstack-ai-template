# Frontend Template Improvements for AI Reproducibility

## Current State Assessment

The template has a solid foundation with:
- ✅ TanStack Router (file-based routing)
- ✅ React Query for server state
- ✅ API client abstraction
- ✅ Auth context
- ✅ Shadcn/ui components
- ✅ Error handling patterns
- ✅ Query key factory

## Critical Gaps for AI Reproducibility

### 1. **Missing API Layer Documentation**
**Problem:** AI agents don't know how to structure API calls or where endpoints are defined.

**Current:** `api-endpoints.ts` exists but is not documented in AGENTS.md or README.
**Fix:** Document API endpoint patterns and conventions.

```tsx
// Example: lib/api-endpoints.ts structure
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

---

### 2. **Undocumented Query Patterns**
**Problem:** AI agents don't know how to create queries following the template's conventions.

**Current:** `query-keys.ts` exists but no examples of actual query functions.
**Fix:** Document `queryOptions` factory pattern and expected structure.

```tsx
// Example: hooks/queries/useItemsQuery.ts (doesn't exist yet)
import { queryOptions } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { ItemResponse } from '@/lib/schemas'

export const itemsQueryOptions = () =>
  queryOptions({
    queryKey: ['items', 'list'],
    queryFn: () => api.get<ItemResponse[]>(API.ITEMS.LIST),
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
```

---

### 3. **No Documented Mutation Patterns**
**Problem:** AI agents don't know standard patterns for mutations (create, update, delete).

**Current:** Components implement mutations inline without clear patterns.
**Fix:** Document reusable mutation hooks with optimistic updates.

```tsx
// Example: hooks/mutations/useCreateItem.ts (doesn't exist yet)
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'

export function useCreateItem() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      api.post(API.ITEMS.CREATE, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.items.all })
    },
  })
}
```

---

### 4. **Missing Component Structure Guidelines**
**Problem:** AI agents don't know where to put components or how to organize them.

**Current:** Mixed component types (UI, dialogs, features) in `/components` folder.
**Fix:** Establish clear folder structure:

```
src/components/
├── ui/                          # shadcn/ui exports only
│   ├── button.tsx
│   ├── input.tsx
│   └── ...
├── common/                       # Reusable feature components
│   ├── Navigation.tsx
│   ├── Layout.tsx
│   └── ErrorBoundary.tsx
├── items/                        # Feature-specific components
│   ├── ItemsList.tsx
│   ├── ItemCard.tsx
│   ├── ItemForm.tsx
│   └── dialogs/
│       ├── CreateItemDialog.tsx
│       ├── EditItemDialog.tsx
│       └── DeleteItemDialog.tsx
└── auth/                         # Auth-specific components
    ├── LoginForm.tsx
    ├── RegisterForm.tsx
    └── ProtectedRoute.tsx
```

---

### 5. **No Error Handling Strategy Documentation**
**Problem:** AI agents don't know how to handle different error types consistently.

**Current:** `error-handler.ts` exists but is undocumented.
**Fix:** Document error handling patterns.

```tsx
// Example usage pattern:
import { useErrorHandler } from '@/hooks/useErrorHandler'

function MyComponent() {
  const { handleError, showError } = useErrorHandler()
  
  const mutation = useMutation({
    mutationFn: () => api.post(...),
    onError: (error) => handleError(error, {
      validationMessage: 'Please check your input',
      networkMessage: 'Check your connection and try again',
    })
  })
}
```

---

### 6. **Missing Data Loading Patterns**
**Problem:** AI agents create ad-hoc loading states instead of reusable patterns.

**Current:** Individual components manage isLoading/isPending states.
**Fix:** Document standard loading + error states pattern.

```tsx
// Example pattern to document:
function ItemsList() {
  const { data, isLoading, error } = useQuery(itemsQueryOptions())
  
  if (isLoading) return <LoadingState />
  if (error) return <ErrorState error={error} />
  return <ListContent items={data} />
}
```

---

### 7. **Incomplete Form Patterns Documentation**
**Problem:** AI agents don't know how to structure forms with validation.

**Current:** react-hook-form + Zod are installed but no examples exist.
**Fix:** Document form pattern with schema-first approach.

```tsx
// Example: hooks/useItemForm.ts
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

export const itemFormSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
})

export type ItemFormData = z.infer<typeof itemFormSchema>

export function useItemForm(defaultValues?: Partial<ItemFormData>) {
  return useForm<ItemFormData>({
    resolver: zodResolver(itemFormSchema),
    defaultValues,
  })
}
```

---

### 8. **Missing Testing Patterns**
**Problem:** AI agents don't know how to structure tests.

**Current:** Vitest + Playwright installed but no test examples exist.
**Fix:** Document testing patterns with examples.

```tsx
// Example: src/components/items/__tests__/ItemCard.test.tsx
import { render, screen } from '@testing-library/react'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import { ItemCard } from '../ItemCard'

describe('ItemCard', () => {
  const queryClient = new QueryClient()
  
  it('renders item details', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ItemCard item={{ id: '1', name: 'Test' }} />
      </QueryClientProvider>
    )
    
    expect(screen.getByText('Test')).toBeInTheDocument()
  })
})
```

---

### 9. **No Protected Route Pattern**
**Problem:** AI agents don't know how to structure auth-protected routes.

**Current:** Auth context exists but no ProtectedRoute component documented.
**Fix:** Document and create ProtectedRoute pattern.

```tsx
// Example: hooks/useProtectedRoute.ts
import { useAuth } from '@/contexts/AuthContext'
import { useNavigate } from '@tanstack/react-router'
import { useEffect } from 'react'

export function useProtectedRoute() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  
  useEffect(() => {
    if (!isAuthenticated) {
      navigate({ to: '/login' })
    }
  }, [isAuthenticated, navigate])
  
  return isAuthenticated
}
```

---

### 10. **Missing Naming Conventions**
**Problem:** AI agents make inconsistent naming choices.

**Fix:** Document conventions:

```
HOOKS:
- useQuery: useItemsList, useItemDetail
- useMutation: useCreateItem, useUpdateItem, useDeleteItem
- Custom: useAuth, useErrorHandler

FILES:
- Hooks: src/hooks/use*.ts
- Queries: src/hooks/queries/use*Query.ts (if queryOptions)
- Mutations: src/hooks/mutations/use*Mutation.ts
- Components: PascalCase files, PascalCase exports
- Utilities: camelCase files, named exports
- Types: src/types/*.ts with .d.ts suffix for globals

COMPONENTS:
- Feature folders: singular name (items/, auth/)
- Sub-components: descriptive names (ItemForm, ItemCard, ItemsList)
- Dialog components: *Dialog suffix
```

---

## Implementation Priority

### 🔴 Critical (Must-Have)
1. Update AGENTS.md with complete frontend patterns
2. Create FRONTEND_ARCHITECTURE.md with structure & patterns
3. Document API endpoint conventions
4. Document query/mutation patterns with examples
5. Create example hooks for queries and mutations

### 🟡 High (Should-Have)
6. Add component folder structure guide
7. Document error handling strategy
8. Add testing pattern examples
9. Create ProtectedRoute pattern
10. Document naming conventions

### 🟢 Nice-To-Have
11. Add CSS/styling conventions guide
12. Create component scaffolding templates
13. Add performance optimization guide
14. Document accessibility checklist

---

## Quick Reference for AI Agents

Once improvements are implemented, this is what AI agents should understand:

```
✅ FOLDER STRUCTURE
- src/components/ui/          → shadcn/ui only
- src/components/common/      → shared features
- src/components/{feature}/   → feature-scoped
- src/hooks/queries/          → queryOptions factories
- src/hooks/mutations/        → mutation hooks
- src/lib/                    → utilities, config, schemas
- src/types/                  → TypeScript types
- src/routes/                 → file-based routing

✅ QUERY PATTERN
const itemsQuery = queryOptions({
  queryKey: ['items', params],
  queryFn: () => api.get(API.ITEMS.LIST),
})

✅ MUTATION PATTERN
const mutation = useMutation({
  mutationFn: (data) => api.post(API.ITEMS.CREATE, data),
  onSuccess: () => queryClient.invalidateQueries(...)
})

✅ FORM PATTERN
const form = useForm({
  resolver: zodResolver(itemFormSchema),
  defaultValues: { ... }
})

✅ PROTECTED ROUTE
- Check isAuthenticated in loader or component
- Redirect to /login if not authenticated

✅ ERROR HANDLING
- api.ts throws ApiError with status, code, fields
- Components use try/catch or onError callbacks
- Show toast for user-facing errors via sonner
```

---

## Files to Create/Update

### Create:
- [ ] `FRONTEND_ARCHITECTURE.md` - Complete guide
- [ ] `src/hooks/queries/use*Query.ts` - Example queries
- [ ] `src/hooks/mutations/use*Mutation.ts` - Example mutations
- [ ] `src/lib/schemas/index.ts` - Centralized Zod schemas
- [ ] `src/hooks/useProtectedRoute.ts` - Route protection
- [ ] `src/hooks/useErrorHandler.ts` - Error handling utility

### Update:
- [ ] `AGENTS.md` - Add architectural patterns section
- [ ] `frontend/README.md` - Link to new architecture doc
- [ ] Example components with comments showing patterns

