# Frontend Architecture Guide

A complete guide to the template's architecture, patterns, and conventions for AI reproducibility.

## Overview

This is a **TanStack Router SPA** (Single Page Application) with:
- **State:** React Query for server state, React Context for UI state
- **Routing:** File-based routing in `src/routes/`
- **API:** Fetch-based client with Bearer token auth
- **Forms:** Schema-first validation with Zod + react-hook-form
- **Styling:** Tailwind CSS v4 + shadcn/ui components
- **Testing:** Vitest (unit) + Playwright (E2E)

## Folder Structure Reference

```
src/
├── components/              # React components (flat — no feature subdirs)
│   ├── ui/                  # shadcn/ui primitives (DO NOT add custom components here)
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── dialog.tsx
│   │   └── ...
│   ├── Navigation.tsx       # App navigation
│   ├── Layout.tsx           # Root layout wrapper
│   ├── ErrorBoundary.tsx    # Error boundary
│   ├── CreateItemDialog.tsx
│   ├── EditItemDialog.tsx
│   ├── DeleteItemDialog.tsx
│   └── ItemFormDialog.tsx   # Shared form used by Create and Edit dialogs
│
├── contexts/                # React Context for UI state
│   └── AuthContext.tsx      # Global auth state
│
├── hooks/                   # React hooks (flat)
│   ├── useItems.ts          # All items queries and mutations
│   └── useDebounce.ts       # Debounce utility hook
│
├── lib/                     # Utilities & configuration
│   ├── api-client.ts        # Fetch wrapper class
│   ├── api-endpoints.ts     # Endpoint URL constants
│   ├── auth.ts              # Token storage functions
│   ├── config.ts            # Runtime config
│   ├── error-handler.ts     # Error handling utilities
│   ├── query-keys.ts        # Query key factory
│   ├── utils.ts             # General utilities
│   ├── web-vitals.ts        # Web Vitals tracking (DEV-only logging)
│   └── schemas/             # Zod validation schemas
│       └── index.ts         # Auth + item schemas (loginSchema, registerSchema, etc.)
│
├── routes/                  # TanStack Router file-based routes
│   ├── __root.tsx           # Root layout & providers
│   ├── index.tsx            # Home page
│   ├── login.tsx            # Login page
│   ├── register.tsx         # Register page
│   └── items.tsx            # Items list page (auth-guarded via beforeLoad)
│
├── types/                   # TypeScript types & interfaces
│   ├── auth.ts              # AuthSessionResponse
│   └── item.ts              # Item, ItemsResponse, ItemsParams
│
├── styles/                  # Global styles
│   ├── app.css              # Main stylesheet (Tailwind imports + CSS vars)
│   └── home.css             # Home page styles (glassmorphism demo)
│
├── test/                    # Testing utilities
│   └── setup.ts             # Vitest setup
│
└── router.tsx               # Router initialization

test/ (project root)
└── e2e/                     # Playwright E2E tests
    ├── auth.spec.ts
    └── items.spec.ts
```

## Detailed Patterns

### 1. API Layer

**File:** `src/lib/api-client.ts`

The API client handles:
- Bearer token injection from localStorage
- Automatic 401 redirect to `/login`
- JSON error parsing
- Typed responses

```tsx
// Usage in components/hooks:
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'

const data = await api.get<ItemResponse[]>(API.ITEMS.LIST)
const created = await api.post<ItemResponse>(API.ITEMS.CREATE, payload)
```

**File:** `src/lib/api-endpoints.ts`

Group endpoints by feature:

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
  // Add more features as needed
} as const
```

---

### 2. Server State with React Query

**Pattern: queryOptions Factory**

File: `src/hooks/queries/useItemsQuery.ts`

```tsx
import { queryOptions, useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import type { ItemResponse } from '@/lib/schemas/items'

// Factory function that returns queryOptions
export const itemsQueryOptions = () =>
  queryOptions({
    queryKey: ['items', 'list'],
    queryFn: () => api.get<ItemResponse[]>(API.ITEMS.LIST),
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: 1,
  })

// Hook that uses the factory
export function useItemsQuery() {
  return useQuery(itemsQueryOptions())
}
```

Usage in components:

```tsx
function ItemsList() {
  const { data, isLoading, error } = useItemsQuery()
  
  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage error={error} />
  
  return (
    <ul>
      {data?.map(item => (
        <li key={item.id}>{item.name}</li>
      ))}
    </ul>
  )
}
```

---

### 3. Mutations

File: `src/hooks/mutations/useCreateItem.ts`

```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'
import type { ItemResponse, ItemCreate } from '@/lib/schemas/items'

export function useCreateItem() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: ItemCreate) =>
      api.post<ItemResponse>(API.ITEMS.CREATE, data),
    
    onSuccess: () => {
      // Invalidate list to trigger refetch
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.items.all 
      })
      
      // Or optimistically update:
      // queryClient.setQueryData(
      //   queryKeys.items.list(),
      //   (old?: ItemResponse[]) => [...(old || []), response]
      // )
    },
    
    onError: (error) => {
      // Error handling happens in components via .mutateAsync()
      console.error('Create failed:', error)
    },
  })
}
```

Usage in components:

```tsx
function CreateItemDialog() {
  const { mutate, isPending, error } = useCreateItem()
  
  const handleSubmit = (formData: ItemCreate) => {
    mutate(formData, {
      onSuccess: () => {
        toast.success('Item created')
        closeDialog()
      },
      onError: (error) => {
        toast.error(error.detail)
      },
    })
  }
  
  return (
    <form onSubmit={handleSubmit}>
      {/* form fields */}
      <button disabled={isPending}>Create</button>
      {error && <div>{error.detail}</div>}
    </form>
  )
}
```

---

### 4. Forms with Validation

File: `src/lib/schemas/items.ts`

```tsx
import { z } from 'zod'

export const itemCreateSchema = z.object({
  name: z.string()
    .min(1, 'Name is required')
    .max(255, 'Name must be less than 255 characters'),
  description: z.string()
    .max(1000, 'Description must be less than 1000 characters')
    .optional()
    .nullable(),
})

export type ItemCreate = z.infer<typeof itemCreateSchema>

export const itemUpdateSchema = itemCreateSchema.partial()
export type ItemUpdate = z.infer<typeof itemUpdateSchema>
```

File: `src/hooks/useItemForm.ts` (optional, if reused)

```tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { itemCreateSchema, type ItemCreate } from '@/lib/schemas/items'

export function useItemForm(defaultValues?: Partial<ItemCreate>) {
  return useForm<ItemCreate>({
    resolver: zodResolver(itemCreateSchema),
    defaultValues: defaultValues || { name: '', description: '' },
  })
}
```

Usage in component:

```tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { itemCreateSchema, type ItemCreate } from '@/lib/schemas/items'
import { Form, FormField, FormItem } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

function ItemForm({ onSubmit }: { onSubmit: (data: ItemCreate) => void }) {
  const form = useForm<ItemCreate>({
    resolver: zodResolver(itemCreateSchema),
    defaultValues: { name: '', description: '' },
  })
  
  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <label>Name</label>
              <Input {...field} />
            </FormItem>
          )}
        />
        
        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <label>Description</label>
              <Input {...field} />
            </FormItem>
          )}
        />
        
        <Button type="submit">Submit</Button>
      </form>
    </Form>
  )
}
```

---

### 5. Authentication

File: `src/contexts/AuthContext.tsx`

The AuthContext manages:
- Token in localStorage
- isAuthenticated boolean
- login/logout methods
- Cache clearing on logout

```tsx
import { useAuth } from '@/contexts/AuthContext'

function Header() {
  const { isAuthenticated, logout } = useAuth()
  
  if (!isAuthenticated) {
    return <Link to="/login">Login</Link>
  }
  
  return (
    <button onClick={() => logout()}>
      Logout
    </button>
  )
}
```

File: `src/routes/__root.tsx`

The root layout wraps the app with providers:

```tsx
<QueryClientProvider client={queryClient}>
  <AuthProvider queryClient={queryClient}>
    <Layout>
      {children}
    </Layout>
  </AuthProvider>
</QueryClientProvider>
```

---

### 6. Protected Routes

Use `beforeLoad` in the route definition to guard protected pages. This runs before the component mounts, avoiding any flash of content.

```tsx
// src/routes/items.tsx
import { createFileRoute, redirect } from '@tanstack/react-router'
import { isAuthenticated } from '@/lib/auth'

export const Route = createFileRoute('/items')({
  beforeLoad: () => {
    if (!isAuthenticated()) {
      throw redirect({ to: '/login', search: { redirect: '/items' } })
    }
  },
  component: ItemsPage,
})
```

`isAuthenticated()` reads from localStorage synchronously — safe to call in `beforeLoad` on both client and server.

---

### 7. Error Handling

**API Errors:**

The `api-client.ts` throws `ApiError` with:
- `status` - HTTP status code
- `message` - Error message from server
- `code` - Error code for programmatic handling
- `fields` - Validation error fields (for forms)

```tsx
try {
  await api.post(API.ITEMS.CREATE, data)
} catch (error) {
  if (error instanceof ApiError) {
    if (error.status === 400 && error.fields) {
      // Handle validation errors
      form.setError('name', { message: error.fields.name?.[0] })
    } else {
      // Handle other errors
      toast.error(error.message)
    }
  }
}
```

**Component Error Handling:**

```tsx
function ItemsList() {
  const { data, isLoading, error } = useItemsQuery()
  
  if (error) {
    return (
      <div className="error-state">
        <h2>Something went wrong</h2>
        <p>{error.message}</p>
        <button onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    )
  }
  
  return <div>Content</div>
}
```

**Global Error Boundary:**

`src/components/ErrorBoundary.tsx` catches React errors:

```tsx
export class ErrorBoundary extends React.Component {
  static getDerivedStateFromError(error) {
    return { error }
  }
  
  render() {
    if (this.state.error) {
      return <div>App crashed: {this.state.error.message}</div>
    }
    return this.props.children
  }
}
```

---

### 8. Component Patterns

**List Component:**

```tsx
// src/components/items/ItemsList.tsx
import { useItemsQuery } from '@/hooks/queries/useItemsQuery'
import { ItemCard } from './ItemCard'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorMessage } from '@/components/common/ErrorMessage'

export function ItemsList() {
  const { data, isLoading, error } = useItemsQuery()
  
  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage error={error} />
  
  return (
    <div className="grid gap-4">
      {data?.map(item => (
        <ItemCard key={item.id} item={item} />
      ))}
    </div>
  )
}
```

**Dialog Component:**

```tsx
// src/components/items/dialogs/CreateItemDialog.tsx
import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader } from '@/components/ui/dialog'
import { ItemForm } from '../ItemForm'
import { useCreateItem } from '@/hooks/mutations/useCreateItem'

export function CreateItemDialog({ open, onOpenChange }) {
  const { mutate, isPending } = useCreateItem()
  
  const handleSubmit = (data) => {
    mutate(data, {
      onSuccess: () => {
        toast.success('Item created')
        onOpenChange(false)
      },
      onError: (error) => {
        toast.error(error.message)
      },
    })
  }
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>Create Item</DialogHeader>
        <ItemForm onSubmit={handleSubmit} isLoading={isPending} />
      </DialogContent>
    </Dialog>
  )
}
```

---

### 9. Testing

**Unit Test Example:**

```tsx
// src/components/items/__tests__/ItemCard.test.tsx
import { render, screen } from '@testing-library/react'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import { ItemCard } from '../ItemCard'

describe('ItemCard', () => {
  const queryClient = new QueryClient()
  const mockItem = {
    id: '1',
    name: 'Test Item',
    description: 'Test Description',
    createdAt: new Date().toISOString(),
  }
  
  it('renders item name', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ItemCard item={mockItem} />
      </QueryClientProvider>
    )
    
    expect(screen.getByText('Test Item')).toBeInTheDocument()
  })
})
```

**E2E Test Example:**

```tsx
// e2e/items.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Items Feature', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('http://localhost:3000/login')
    await page.fill('[name="email"]', 'test@example.com')
    await page.fill('[name="password"]', 'password')
    await page.click('button:has-text("Login")')
    await page.waitForNavigation()
  })
  
  test('create new item', async ({ page }) => {
    await page.goto('http://localhost:3000/items')
    await page.click('button:has-text("Create")')
    
    await page.fill('[name="name"]', 'New Item')
    await page.fill('[name="description"]', 'Test description')
    await page.click('button:has-text("Submit")')
    
    await expect(page.locator('text=New Item')).toBeVisible()
  })
})
```

---

### 10. Naming Conventions Reference

| Type | Location | Pattern | Example |
|------|----------|---------|---------|
| Feature Hooks | `hooks/` | `use*.ts` | `useItems.ts` |
| Utility Hooks | `hooks/` | `use*.ts` | `useDebounce.ts` |
| Components | `components/` | `*.tsx` (named exports) | `Navigation.tsx` |
| Dialogs | `components/` | `*Dialog.tsx` | `CreateItemDialog.tsx` |
| Route Pages | `routes/` | `*.tsx` | `items.tsx` |
| Schemas | `lib/schemas/` | `*.ts` | `index.ts` |
| Types | `types/` | `*.ts` | `item.ts` |
| Utils | `lib/` | `*.ts` (named exports) | `utils.ts` |

---

## Common Workflows

### Adding a New Feature

1. **Create API endpoints** in `lib/api-endpoints.ts`
2. **Create Zod schemas** in `lib/schemas/index.ts`
3. **Create hook** in `hooks/use{Feature}.ts` (queries and mutations together)
4. **Create components** in `components/` (flat — no subdirectory)
5. **Create route** in `routes/{feature}.tsx`
6. **Add tests** co-located with the hook (`hooks/use{Feature}.test.ts`)

### Adding Authentication-Required Route

```tsx
// src/routes/protected-feature.tsx
import { createFileRoute, redirect } from '@tanstack/react-router'
import { isAuthenticated } from '@/lib/auth'

export const Route = createFileRoute('/protected-feature')({
  beforeLoad: () => {
    if (!isAuthenticated()) {
      throw redirect({ to: '/login', search: { redirect: '/protected-feature' } })
    }
  },
  component: ProtectedFeature,
})

function ProtectedFeature() {
  return <div>Protected content</div>
}
```

### Handling Form Validation Errors

```tsx
const { mutate } = useCreateItem()

mutate(data, {
  onError: (error) => {
    if (error.status === 422 && error.fields) {
      // Field-level errors
      Object.entries(error.fields).forEach(([field, messages]) => {
        form.setError(field as any, { 
          message: messages[0] 
        })
      })
    } else {
      // General error
      toast.error(error.message)
    }
  },
})
```

---

## Environment Variables

**File:** `.env.example`

```
VITE_API_BASE_URL=http://localhost:9095
```

Access in code:

```tsx
import { config } from '@/lib/config'

const baseUrl = config.apiBaseUrl
```

---

## Development Checklist

- [ ] Query hooks use `queryOptions` factory pattern
- [ ] Mutations invalidate relevant cache
- [ ] Forms use Zod schemas
- [ ] Components are in `components/` (no feature subdirectories)
- [ ] API endpoints are defined in `api-endpoints.ts`
- [ ] Errors are handled with try/catch or onError callbacks
- [ ] Protected routes check `isAuthenticated`
- [ ] Tests are co-located with source files (`use*.test.ts`, `*.test.ts`)
- [ ] Types are defined in `lib/schemas/` or `types/`
- [ ] Components follow shadcn/ui patterns

---

## Quick Debugging

**React Query state:**
- Open React Query DevTools (bottom right)
- Inspect query/mutation status
- Check cache age with "Stale Time" indicator

**Router state:**
- Open React Router DevTools (bottom right)
- Inspect route transitions
- Check matched routes

**API calls:**
- Check browser Network tab
- Verify Authorization header (should have Bearer token)
- Check response status and error fields

**Component state:**
- Use React DevTools
- Inspect component props
- Check context values

