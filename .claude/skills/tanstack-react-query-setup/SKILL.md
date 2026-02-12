---
name: tanstack-react-query-setup
description: Configure TanStack Query (React Query) with QueryClient, provider, devtools, and optimal defaults. SHARED skill for both TanStack Start (SSR) and TanStack Router (SPA).
---

# TanStack Query Setup

## Overview

This skill covers setting up TanStack Query (formerly React Query) in TanStack Start or TanStack Router projects. TanStack Query provides powerful asynchronous state management for data fetching, caching, and synchronization.

**Important:** This skill works for both:
- TanStack Start (SSR full-stack)
- TanStack Router (SPA client-only)

## Prerequisites

- Existing TanStack Start or TanStack Router project
- Bun or npm package manager
- Node.js 18+

## Step 1: Install TanStack Query

Install the core package and devtools:

```bash
bun add @tanstack/react-query @tanstack/react-query-devtools
```

Or with npm:

```bash
npm install @tanstack/react-query @tanstack/react-query-devtools
```

## Step 2: Create QueryClient Configuration

Create `src/lib/query-client.ts` with optimal defaults:

```typescript
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Time before data is considered stale (5 minutes)
      staleTime: 1000 * 60 * 5,
      // Time before inactive queries are garbage collected (10 minutes)
      gcTime: 1000 * 60 * 10,
      // Retry failed requests 3 times with exponential backoff
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      // Refetch on window focus in production
      refetchOnWindowFocus: process.env.NODE_ENV === 'production',
      // Don't refetch on mount if data is fresh
      refetchOnMount: false,
    },
    mutations: {
      // Retry failed mutations once
      retry: 1,
    },
  },
})
```

### Configuration Options Explained

| Option | Default | Description |
|--------|---------|-------------|
| `staleTime` | 5 minutes | How long data is considered fresh |
| `gcTime` | 10 minutes | How long inactive data is kept in cache |
| `retry` | 3 | Number of retry attempts on failure |
| `retryDelay` | Exponential | Delay between retry attempts |
| `refetchOnWindowFocus` | true (prod) | Refetch when user returns to tab |
| `refetchOnMount` | false | Refetch when component mounts |

## Step 3: Create Query Provider Component

Create `src/components/query-provider.tsx`:

```tsx
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { queryClient } from '~/lib/query-client'

type QueryProviderProps = {
  children: React.ReactNode
}

export function QueryProvider({ children }: QueryProviderProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} position="bottom" />
    </QueryClientProvider>
  )
}
```

### Devtools Configuration

The devtools panel provides:
- Query cache inspection
- Mutation tracking
- Network request timeline
- Cache invalidation tools

**Options:**
- `initialIsOpen`: Start with devtools open/closed
- `position`: 'top' | 'bottom' | 'left' | 'right'
- `buttonPosition`: Where to place the toggle button

## Step 4: Add Provider to App

### For TanStack Start

Update `src/routes/__root.tsx`:

```tsx
import { createRootRoute, Outlet } from '@tanstack/react-router'
import { Meta, Scripts } from '@tanstack/react-start'
import { QueryProvider } from '~/components/query-provider'
import '../app.css'

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
    ],
  }),
  component: () => (
    <html>
      <head>
        <Meta />
      </head>
      <body>
        <QueryProvider>
          <Outlet />
        </QueryProvider>
        <Scripts />
      </body>
    </html>
  ),
})
```

### For TanStack Router (SPA)

Update your entry point `src/main.tsx`:

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { QueryProvider } from '~/components/query-provider'
import { routeTree } from './routeTree.gen'
import './app.css'

const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

const rootElement = document.getElementById('root')!
if (!rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement)
  root.render(
    <React.StrictMode>
      <QueryProvider>
        <RouterProvider router={router} />
      </QueryProvider>
    </React.StrictMode>
  )
}
```

## Step 5: Create Your First Query

Create a simple query to test the setup:

```tsx
import { useQuery } from '@tanstack/react-query'

export function UserProfile() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['user', 'profile'],
    queryFn: async () => {
      const response = await fetch('/api/user/profile')
      if (!response.ok) throw new Error('Failed to fetch user')
      return response.json()
    },
  })

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>

  return (
    <div>
      <h1>{data.name}</h1>
      <p>{data.email}</p>
    </div>
  )
}
```

## Step 6: Environment-Specific Configuration

For production optimizations, create separate configs:

```typescript
// src/lib/query-client.ts
import { QueryClient } from '@tanstack/react-query'

const isDevelopment = process.env.NODE_ENV === 'development'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: isDevelopment ? 0 : 1000 * 60 * 5,
      gcTime: isDevelopment ? 1000 * 60 * 5 : 1000 * 60 * 10,
      retry: isDevelopment ? 1 : 3,
      refetchOnWindowFocus: !isDevelopment,
      refetchOnMount: isDevelopment,
    },
  },
})
```

## Step 7: SSR-Specific Setup (TanStack Start Only)

For server-side rendering with TanStack Start, configure hydration:

```typescript
// src/lib/query-client.ts
import { QueryClient, isServer } from '@tanstack/react-query'

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 1000 * 60 * 5,
        gcTime: 1000 * 60 * 10,
      },
    },
  })
}

let browserQueryClient: QueryClient | undefined = undefined

export function getQueryClient() {
  if (isServer) {
    // Server: always create a new QueryClient
    return makeQueryClient()
  } else {
    // Browser: reuse singleton QueryClient
    if (!browserQueryClient) browserQueryClient = makeQueryClient()
    return browserQueryClient
  }
}
```

Update provider for SSR:

```tsx
// src/components/query-provider.tsx
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { getQueryClient } from '~/lib/query-client'

type QueryProviderProps = {
  children: React.ReactNode
}

export function QueryProvider({ children }: QueryProviderProps) {
  const queryClient = getQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
```

## Verification

After setup, verify:

1. **Provider works:** Component tree has access to `useQuery`
2. **Devtools appear:** Click devtools button to inspect queries
3. **Queries execute:** Test query fetches and caches data
4. **Cache persists:** Navigate away and back, data should be cached
5. **SSR hydrates:** (TanStack Start) Server data hydrates without refetch

Example verification component:

```tsx
import { useQuery } from '@tanstack/react-query'

export function HealthCheck() {
  const { data, isLoading, dataUpdatedAt } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const response = await fetch('https://api.github.com/zen')
      return response.text()
    },
  })

  return (
    <div className="p-4 border rounded">
      <h2 className="font-bold">TanStack Query Health Check</h2>
      {isLoading ? (
        <p>Loading...</p>
      ) : (
        <>
          <p className="mt-2">{data}</p>
          <p className="text-xs text-muted-foreground mt-2">
            Last updated: {new Date(dataUpdatedAt).toLocaleTimeString()}
          </p>
        </>
      )}
    </div>
  )
}
```

## Common Issues

### Issue: "No QueryClient set"

**Cause:** Component rendered outside QueryProvider
**Solution:** Ensure QueryProvider wraps your component tree in `__root.tsx`

### Issue: Queries refetching too often

**Cause:** staleTime is too low
**Solution:** Increase `staleTime` in QueryClient config

### Issue: Devtools not showing

**Cause:** Devtools only show in development
**Solution:** Check `NODE_ENV` and ensure devtools are included

### Issue: SSR hydration mismatch

**Cause:** Server and client QueryClient instances differ
**Solution:** Use `getQueryClient()` pattern for SSR

## Advanced Configuration

### Persisting Cache to LocalStorage

```bash
bun add @tanstack/react-query-persist-client
```

```typescript
import { QueryClient } from '@tanstack/react-query'
import { persistQueryClient } from '@tanstack/react-query-persist-client'
import { createSyncStoragePersister } from '@tanstack/query-sync-storage-persister'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      gcTime: 1000 * 60 * 60 * 24, // 24 hours
    },
  },
})

const persister = createSyncStoragePersister({
  storage: window.localStorage,
})

persistQueryClient({
  queryClient,
  persister,
})
```

### Global Error Handling

```typescript
import { QueryClient } from '@tanstack/react-query'
import { toast } from '~/components/ui/use-toast'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      onError: (error) => {
        toast({
          variant: 'destructive',
          title: 'Query Error',
          description: error.message,
        })
      },
    },
    mutations: {
      onError: (error) => {
        toast({
          variant: 'destructive',
          title: 'Mutation Error',
          description: error.message,
        })
      },
    },
  },
})
```

## Project Structure After Setup

```
your-project/
├── src/
│   ├── components/
│   │   └── query-provider.tsx    # Query provider wrapper
│   ├── lib/
│   │   └── query-client.ts       # QueryClient configuration
│   ├── routes/                   # TanStack routes
│   │   └── __root.tsx            # Root with QueryProvider
│   └── app.css                   # Global styles
├── tsconfig.json
└── vite.config.ts
```

## Notes

- TanStack Query handles caching, refetching, and state management automatically
- Devtools are essential for debugging query behavior
- SSR requires careful QueryClient singleton management
- Default options apply to all queries unless overridden
- Query keys should be arrays for better cache management
- staleTime and gcTime are the most important config options

## Next Steps

After setup:
- Create query patterns and conventions (see `tanstack-react-query-patterns` skill)
- Implement mutation patterns (see `tanstack-react-query-mutations` skill)
- Set up API layer with fetch wrapper (see `tanstack-client-api-layer` skill)
- Add authentication integration (see `tanstack-client-auth` skill)

## Resources

- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [TanStack Query Devtools](https://tanstack.com/query/latest/docs/react/devtools)
- [Query Keys Best Practices](https://tanstack.com/query/latest/docs/react/guides/query-keys)
- [SSR Guide](https://tanstack.com/query/latest/docs/react/guides/ssr)
