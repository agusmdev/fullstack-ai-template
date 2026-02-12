---
name: tanstack-react-query-patterns
description: Query patterns with queryOptions factory, key conventions, prefetching strategies, and type-safe reusable query definitions. SHARED skill for both TanStack Start (SSR) and TanStack Router (SPA).
---

# TanStack Query Patterns

## Overview

This skill covers best practices and patterns for organizing TanStack Query code, including query key conventions, queryOptions factories, prefetching, dependent queries, and type-safe query definitions.

**Important:** This skill works for both:
- TanStack Start (SSR full-stack)
- TanStack Router (SPA client-only)

## Prerequisites

- TanStack Query installed and configured (see `tanstack-react-query-setup` skill)
- Understanding of React hooks
- Basic TypeScript knowledge

## Pattern 1: Query Key Conventions

Query keys are the foundation of TanStack Query's caching. Use consistent conventions:

### Hierarchical Key Structure

```typescript
// src/lib/query-keys.ts
export const queryKeys = {
  // Entity-based keys
  users: {
    all: ['users'] as const,
    lists: () => [...queryKeys.users.all, 'list'] as const,
    list: (filters: UserFilters) => [...queryKeys.users.lists(), filters] as const,
    details: () => [...queryKeys.users.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.users.details(), id] as const,
  },
  posts: {
    all: ['posts'] as const,
    lists: () => [...queryKeys.posts.all, 'list'] as const,
    list: (filters: PostFilters) => [...queryKeys.posts.lists(), filters] as const,
    details: () => [...queryKeys.posts.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.posts.details(), id] as const,
  },
} as const

// Usage examples:
// ['users'] - all user-related queries
// ['users', 'list'] - all user list queries
// ['users', 'list', { status: 'active' }] - filtered user list
// ['users', 'detail'] - all user detail queries
// ['users', 'detail', '123'] - specific user detail
```

### Benefits

1. **Easy invalidation:** `invalidateQueries(['users'])` clears all user queries
2. **Specific targeting:** `invalidateQueries(['users', 'detail', userId])` only clears one
3. **Type safety:** `as const` enables TypeScript autocompletion
4. **Consistent structure:** All developers follow same pattern

## Pattern 2: queryOptions Factory

The `queryOptions` factory creates reusable, type-safe query definitions:

### Basic queryOptions

```typescript
// src/queries/user.queries.ts
import { queryOptions } from '@tanstack/react-query'
import { fetchUser, fetchUsers } from '~/api/users'
import { queryKeys } from '~/lib/query-keys'

export const userQueries = {
  detail: (userId: string) =>
    queryOptions({
      queryKey: queryKeys.users.detail(userId),
      queryFn: () => fetchUser(userId),
      staleTime: 1000 * 60 * 5, // 5 minutes
    }),

  list: (filters: UserFilters) =>
    queryOptions({
      queryKey: queryKeys.users.list(filters),
      queryFn: () => fetchUsers(filters),
      staleTime: 1000 * 60 * 2, // 2 minutes
    }),
}
```

### Usage in Components

```tsx
import { useQuery } from '@tanstack/react-query'
import { userQueries } from '~/queries/user.queries'

export function UserProfile({ userId }: { userId: string }) {
  const { data, isLoading, error } = useQuery(userQueries.detail(userId))

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

### Benefits

1. **DRY:** Define query once, use everywhere
2. **Type safety:** TypeScript infers return types
3. **Centralized config:** Change staleTime in one place
4. **Easy testing:** Mock query definitions
5. **IDE support:** Autocomplete for query definitions

## Pattern 3: Prefetching Data

Prefetch data before it's needed for instant UX:

### Prefetch on Route Load (TanStack Start)

```tsx
// src/routes/users/$userId.tsx
import { createFileRoute } from '@tanstack/react-router'
import { userQueries } from '~/queries/user.queries'
import { queryClient } from '~/lib/query-client'

export const Route = createFileRoute('/users/$userId')({
  loader: async ({ params }) => {
    // Prefetch user data during route navigation
    await queryClient.ensureQueryData(userQueries.detail(params.userId))
  },
  component: UserDetail,
})

function UserDetail() {
  const { userId } = Route.useParams()
  const { data } = useQuery(userQueries.detail(userId))
  // Data is already cached from loader, renders instantly
  return <div>{data.name}</div>
}
```

### Prefetch on Hover

```tsx
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { userQueries } from '~/queries/user.queries'

export function UserListItem({ userId }: { userId: string }) {
  const queryClient = useQueryClient()

  const handleMouseEnter = () => {
    // Prefetch when user hovers over link
    queryClient.prefetchQuery(userQueries.detail(userId))
  }

  return (
    <Link
      to="/users/$userId"
      params={{ userId }}
      onMouseEnter={handleMouseEnter}
    >
      View User {userId}
    </Link>
  )
}
```

### Prefetch on Parent Load

```tsx
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { userQueries } from '~/queries/user.queries'

export function UsersList() {
  const queryClient = useQueryClient()
  const { data: users } = useQuery(userQueries.list({}))

  // Prefetch all user details when list loads
  users?.forEach((user) => {
    queryClient.prefetchQuery(userQueries.detail(user.id))
  })

  return (
    <ul>
      {users?.map((user) => (
        <li key={user.id}>
          <Link to="/users/$userId" params={{ userId: user.id }}>
            {user.name}
          </Link>
        </li>
      ))}
    </ul>
  )
}
```

## Pattern 4: Dependent Queries

Queries that depend on data from other queries:

### Sequential Dependencies

```tsx
import { useQuery } from '@tanstack/react-query'
import { userQueries } from '~/queries/user.queries'
import { postQueries } from '~/queries/post.queries'

export function UserPosts({ userId }: { userId: string }) {
  // First query
  const { data: user } = useQuery(userQueries.detail(userId))

  // Second query only runs when user is loaded
  const { data: posts, isLoading: postsLoading } = useQuery({
    ...postQueries.list({ authorId: user?.id }),
    enabled: !!user?.id, // Only run when user.id exists
  })

  if (!user) return <div>Loading user...</div>
  if (postsLoading) return <div>Loading posts...</div>

  return (
    <div>
      <h1>{user.name}'s Posts</h1>
      {posts?.map((post) => (
        <article key={post.id}>{post.title}</article>
      ))}
    </div>
  )
}
```

### Parallel Queries with Dependency

```tsx
import { useQueries } from '@tanstack/react-query'
import { postQueries } from '~/queries/post.queries'

export function PostsByIds({ postIds }: { postIds: string[] }) {
  const results = useQueries({
    queries: postIds.map((id) => postQueries.detail(id)),
  })

  const isLoading = results.some((result) => result.isLoading)
  const posts = results.map((result) => result.data).filter(Boolean)

  if (isLoading) return <div>Loading posts...</div>

  return (
    <div>
      {posts.map((post) => (
        <article key={post.id}>{post.title}</article>
      ))}
    </div>
  )
}
```

## Pattern 5: Conditional Queries

Only run queries when certain conditions are met:

### Authenticated User Queries

```tsx
import { useQuery } from '@tanstack/react-query'
import { userQueries } from '~/queries/user.queries'
import { useAuth } from '~/hooks/use-auth'

export function CurrentUserProfile() {
  const { isAuthenticated, userId } = useAuth()

  const { data: user } = useQuery({
    ...userQueries.detail(userId!),
    enabled: isAuthenticated && !!userId,
  })

  if (!isAuthenticated) return <div>Please log in</div>
  if (!user) return <div>Loading...</div>

  return <div>{user.name}</div>
}
```

### Permission-Based Queries

```tsx
import { useQuery } from '@tanstack/react-query'
import { adminQueries } from '~/queries/admin.queries'
import { useAuth } from '~/hooks/use-auth'

export function AdminDashboard() {
  const { hasPermission } = useAuth()
  const canViewAnalytics = hasPermission('analytics:read')

  const { data: analytics } = useQuery({
    ...adminQueries.analytics(),
    enabled: canViewAnalytics,
  })

  if (!canViewAnalytics) return <div>Access denied</div>

  return <div>{analytics?.totalUsers} users</div>
}
```

## Pattern 6: Infinite Queries

For paginated data with "load more" functionality:

### Basic Infinite Query

```typescript
// src/queries/post.queries.ts
import { infiniteQueryOptions } from '@tanstack/react-query'
import { fetchPosts } from '~/api/posts'
import { queryKeys } from '~/lib/query-keys'

export const postQueries = {
  infinite: (filters: PostFilters) =>
    infiniteQueryOptions({
      queryKey: [...queryKeys.posts.list(filters), 'infinite'],
      queryFn: ({ pageParam }) => fetchPosts({ ...filters, page: pageParam }),
      initialPageParam: 1,
      getNextPageParam: (lastPage, allPages) => {
        return lastPage.hasMore ? allPages.length + 1 : undefined
      },
      getPreviousPageParam: (firstPage, allPages) => {
        return allPages.length > 1 ? allPages.length - 1 : undefined
      },
    }),
}
```

### Usage in Component

```tsx
import { useInfiniteQuery } from '@tanstack/react-query'
import { postQueries } from '~/queries/post.queries'

export function InfinitePostList() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery(postQueries.infinite({}))

  return (
    <div>
      {data?.pages.map((page) =>
        page.posts.map((post) => (
          <article key={post.id}>{post.title}</article>
        ))
      )}
      {hasNextPage && (
        <button
          onClick={() => fetchNextPage()}
          disabled={isFetchingNextPage}
        >
          {isFetchingNextPage ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  )
}
```

## Pattern 7: Placeholder Data

Show stale data while fetching fresh data:

### Using Previous Data

```tsx
import { useQuery } from '@tanstack/react-query'
import { postQueries } from '~/queries/post.queries'

export function PostList({ filters }: { filters: PostFilters }) {
  const { data, isPlaceholderData } = useQuery({
    ...postQueries.list(filters),
    placeholderData: (previousData) => previousData,
  })

  return (
    <div className={isPlaceholderData ? 'opacity-50' : ''}>
      {data?.map((post) => (
        <article key={post.id}>{post.title}</article>
      ))}
    </div>
  )
}
```

### Static Placeholder

```tsx
import { useQuery } from '@tanstack/react-query'
import { userQueries } from '~/queries/user.queries'

const PLACEHOLDER_USER = {
  id: '',
  name: 'Loading...',
  email: 'loading@example.com',
}

export function UserProfile({ userId }: { userId: string }) {
  const { data } = useQuery({
    ...userQueries.detail(userId),
    placeholderData: PLACEHOLDER_USER,
  })

  return <div>{data.name}</div>
}
```

## Pattern 8: Select Transformations

Transform query data before it reaches components:

### Filtering Data

```tsx
import { useQuery } from '@tanstack/react-query'
import { postQueries } from '~/queries/post.queries'

export function PublishedPosts() {
  const { data: publishedPosts } = useQuery({
    ...postQueries.list({}),
    select: (data) => data.filter((post) => post.status === 'published'),
  })

  return (
    <div>
      {publishedPosts?.map((post) => (
        <article key={post.id}>{post.title}</article>
      ))}
    </div>
  )
}
```

### Computing Derived Data

```tsx
import { useQuery } from '@tanstack/react-query'
import { userQueries } from '~/queries/user.queries'

export function UserStats({ userId }: { userId: string }) {
  const { data: stats } = useQuery({
    ...userQueries.detail(userId),
    select: (user) => ({
      fullName: `${user.firstName} ${user.lastName}`,
      age: new Date().getFullYear() - new Date(user.birthDate).getFullYear(),
      isAdult: user.age >= 18,
    }),
  })

  return <div>{stats.fullName} is {stats.age} years old</div>
}
```

## Pattern 9: Optimistic Updates

Update UI immediately before server response:

```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '~/lib/query-keys'
import { updatePost } from '~/api/posts'

export function useUpdatePost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: updatePost,
    onMutate: async (newPost) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.posts.detail(newPost.id) })

      // Snapshot previous value
      const previousPost = queryClient.getQueryData(queryKeys.posts.detail(newPost.id))

      // Optimistically update
      queryClient.setQueryData(queryKeys.posts.detail(newPost.id), newPost)

      return { previousPost }
    },
    onError: (err, newPost, context) => {
      // Rollback on error
      queryClient.setQueryData(
        queryKeys.posts.detail(newPost.id),
        context?.previousPost
      )
    },
    onSettled: (newPost) => {
      // Refetch after error or success
      queryClient.invalidateQueries({ queryKey: queryKeys.posts.detail(newPost.id) })
    },
  })
}
```

## Pattern 10: Custom Hooks

Encapsulate query logic in custom hooks:

```typescript
// src/hooks/use-current-user.ts
import { useQuery } from '@tanstack/react-query'
import { userQueries } from '~/queries/user.queries'
import { useAuth } from './use-auth'

export function useCurrentUser() {
  const { userId, isAuthenticated } = useAuth()

  const query = useQuery({
    ...userQueries.detail(userId!),
    enabled: isAuthenticated && !!userId,
  })

  return {
    ...query,
    user: query.data,
    isAuthenticated,
  }
}
```

```tsx
// Usage
import { useCurrentUser } from '~/hooks/use-current-user'

export function Header() {
  const { user, isAuthenticated } = useCurrentUser()

  return (
    <header>
      {isAuthenticated ? `Hello, ${user?.name}` : 'Please log in'}
    </header>
  )
}
```

## Project Structure

Recommended organization:

```
src/
├── queries/                    # Query definitions
│   ├── user.queries.ts
│   ├── post.queries.ts
│   └── comment.queries.ts
├── lib/
│   ├── query-client.ts        # QueryClient config
│   └── query-keys.ts          # Query key factory
├── hooks/                      # Custom query hooks
│   ├── use-current-user.ts
│   └── use-posts.ts
└── api/                        # API functions
    ├── users.ts
    ├── posts.ts
    └── comments.ts
```

## Best Practices

### DO

✅ Use queryOptions factory for reusability
✅ Keep query keys consistent and hierarchical
✅ Prefetch data for better UX
✅ Use `enabled` for conditional queries
✅ Leverage `select` for data transformations
✅ Implement optimistic updates for mutations
✅ Extract query logic into custom hooks

### DON'T

❌ Inline query definitions everywhere
❌ Use inconsistent query key structures
❌ Fetch data on every render
❌ Ignore error handling
❌ Forget to clean up stale queries
❌ Over-invalidate (invalidating too broadly)
❌ Mix business logic with query definitions

## Common Patterns Summary

| Pattern | Use Case | Key Feature |
|---------|----------|-------------|
| queryOptions | Reusable queries | Type-safe, DRY |
| Query Keys | Cache organization | Hierarchical structure |
| Prefetching | Instant UX | Data ready before needed |
| Dependent Queries | Sequential data | `enabled` option |
| Infinite Queries | Pagination | Load more functionality |
| Placeholder Data | Smooth transitions | Show stale while fetching |
| Select | Data transformation | Compute derived state |
| Optimistic Updates | Instant feedback | Update before server |

## Next Steps

After mastering query patterns:
- Implement mutation patterns (see `tanstack-react-query-mutations` skill)
- Set up API layer with fetch wrapper (see `tanstack-client-api-layer` skill)
- Add authentication integration (see `tanstack-client-auth` skill)
- Build form handling (see `tanstack-shadcn-forms` skill)

## Resources

- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [Query Keys Guide](https://tanstack.com/query/latest/docs/react/guides/query-keys)
- [Query Functions](https://tanstack.com/query/latest/docs/react/guides/query-functions)
- [Dependent Queries](https://tanstack.com/query/latest/docs/react/guides/dependent-queries)
- [Infinite Queries](https://tanstack.com/query/latest/docs/react/guides/infinite-queries)
