---
name: tanstack-client-api-layer
description: API client setup with fetch wrapper, error handling, authentication headers, and React Query integration for TanStack Start/Router.
---

# TanStack Client API Layer

## Overview

This skill covers setting up a robust API client layer for TanStack Start or TanStack Router projects. It includes a type-safe fetch wrapper, centralized error handling, authentication token management, and React Query integration.

**Important:** This skill works for both:
- TanStack Start (SSR full-stack)
- TanStack Router (SPA client-only)

## Prerequisites

- Existing TanStack Start or TanStack Router project
- React Query installed (see `tanstack-react-query-setup` skill)
- TypeScript configured with path aliases

## Architecture Overview

The API client layer consists of:

1. **API Client** - Central fetch wrapper with error handling
2. **Error Types** - Custom error classes for different error scenarios
3. **Response Types** - Shared TypeScript interfaces for API responses
4. **Interceptors** - Request/response middleware for auth headers and logging
5. **React Query Integration** - Helper functions for mutations and queries

## Step 1: Create Error Types

Create `src/lib/api/errors.ts`:

```typescript
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'Network request failed') {
    super(message)
    this.name = 'NetworkError'
  }
}

export class ValidationError extends ApiError {
  constructor(
    message: string,
    public errors: Record<string, string[]>,
    data?: unknown
  ) {
    super(message, 422, data)
    this.name = 'ValidationError'
  }
}

export class UnauthorizedError extends ApiError {
  constructor(message: string = 'Unauthorized', data?: unknown) {
    super(message, 401, data)
    this.name = 'UnauthorizedError'
  }
}

export class ForbiddenError extends ApiError {
  constructor(message: string = 'Forbidden', data?: unknown) {
    super(message, 403, data)
    this.name = 'ForbiddenError'
  }
}

export class NotFoundError extends ApiError {
  constructor(message: string = 'Resource not found', data?: unknown) {
    super(message, 404, data)
    this.name = 'NotFoundError'
  }
}
```

## Step 2: Create Response Types

Create `src/lib/api/types.ts`:

```typescript
export interface ApiResponse<T = unknown> {
  data: T
  message?: string
  errors?: Record<string, string[]>
}

export interface PaginatedResponse<T> {
  data: T[]
  meta: {
    current_page: number
    per_page: number
    total: number
    last_page: number
  }
}

export type ApiMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export interface RequestConfig extends RequestInit {
  params?: Record<string, string | number | boolean>
  timeout?: number
}
```

## Step 3: Create API Client

Create `src/lib/api/client.ts`:

```typescript
import {
  ApiError,
  NetworkError,
  ValidationError,
  UnauthorizedError,
  ForbiddenError,
  NotFoundError,
} from './errors'
import type { RequestConfig } from './types'

class ApiClient {
  private baseURL: string
  private defaultHeaders: HeadersInit

  constructor(baseURL: string = '') {
    this.baseURL = baseURL || import.meta.env.VITE_API_URL || ''
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    }
  }

  /**
   * Set base URL for all requests
   */
  setBaseURL(url: string) {
    this.baseURL = url
  }

  /**
   * Set default headers for all requests
   */
  setDefaultHeaders(headers: HeadersInit) {
    this.defaultHeaders = { ...this.defaultHeaders, ...headers }
  }

  /**
   * Add authentication token to default headers
   */
  setAuthToken(token: string | null) {
    if (token) {
      this.defaultHeaders = {
        ...this.defaultHeaders,
        Authorization: `Bearer ${token}`,
      }
    } else {
      const { Authorization, ...rest } = this.defaultHeaders as Record<string, string>
      this.defaultHeaders = rest
    }
  }

  /**
   * Build URL with query parameters
   */
  private buildURL(endpoint: string, params?: Record<string, string | number | boolean>): string {
    const url = new URL(endpoint, this.baseURL)

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, String(value))
      })
    }

    return url.toString()
  }

  /**
   * Handle API errors and throw appropriate error types
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    const contentType = response.headers.get('content-type')
    const isJson = contentType?.includes('application/json')

    let data: unknown
    try {
      data = isJson ? await response.json() : await response.text()
    } catch (error) {
      throw new ApiError('Failed to parse response', response.status)
    }

    if (!response.ok) {
      const message =
        (isJson && typeof data === 'object' && data && 'message' in data)
          ? String(data.message)
          : response.statusText

      switch (response.status) {
        case 401:
          throw new UnauthorizedError(message, data)
        case 403:
          throw new ForbiddenError(message, data)
        case 404:
          throw new NotFoundError(message, data)
        case 422:
          const errors =
            (isJson && typeof data === 'object' && data && 'errors' in data)
              ? (data.errors as Record<string, string[]>)
              : {}
          throw new ValidationError(message, errors, data)
        default:
          throw new ApiError(message, response.status, data)
      }
    }

    return data as T
  }

  /**
   * Core fetch method with timeout support
   */
  private async fetchWithTimeout(
    url: string,
    config: RequestConfig
  ): Promise<Response> {
    const { timeout = 30000, ...fetchConfig } = config

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeout)

    try {
      const response = await fetch(url, {
        ...fetchConfig,
        signal: controller.signal,
      })
      clearTimeout(timeoutId)
      return response
    } catch (error) {
      clearTimeout(timeoutId)

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new NetworkError('Request timeout')
        }
        throw new NetworkError(error.message)
      }

      throw new NetworkError('Unknown network error')
    }
  }

  /**
   * Generic request method
   */
  async request<T = unknown>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<T> {
    const { params, headers, ...restConfig } = config

    const url = this.buildURL(endpoint, params)

    const mergedHeaders = {
      ...this.defaultHeaders,
      ...headers,
    }

    const response = await this.fetchWithTimeout(url, {
      ...restConfig,
      headers: mergedHeaders,
    })

    return this.handleResponse<T>(response)
  }

  /**
   * GET request
   */
  async get<T = unknown>(
    endpoint: string,
    config?: RequestConfig
  ): Promise<T> {
    return this.request<T>(endpoint, { ...config, method: 'GET' })
  }

  /**
   * POST request
   */
  async post<T = unknown>(
    endpoint: string,
    body?: unknown,
    config?: RequestConfig
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'POST',
      body: JSON.stringify(body),
    })
  }

  /**
   * PUT request
   */
  async put<T = unknown>(
    endpoint: string,
    body?: unknown,
    config?: RequestConfig
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PUT',
      body: JSON.stringify(body),
    })
  }

  /**
   * PATCH request
   */
  async patch<T = unknown>(
    endpoint: string,
    body?: unknown,
    config?: RequestConfig
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PATCH',
      body: JSON.stringify(body),
    })
  }

  /**
   * DELETE request
   */
  async delete<T = unknown>(
    endpoint: string,
    config?: RequestConfig
  ): Promise<T> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' })
  }
}

// Export singleton instance
export const apiClient = new ApiClient()

// Export class for testing/custom instances
export { ApiClient }
```

## Step 4: Create Environment Configuration

Add to `.env` or `.env.local`:

```bash
VITE_API_URL=http://localhost:8000
```

For production:

```bash
VITE_API_URL=https://api.yourapp.com
```

## Step 5: Create API Service Example

Create `src/lib/api/services/users.ts`:

```typescript
import { apiClient } from '../client'
import type { ApiResponse } from '../types'

export interface User {
  id: number
  email: string
  name: string
  created_at: string
  updated_at: string
}

export interface CreateUserDto {
  email: string
  name: string
  password: string
}

export interface UpdateUserDto {
  email?: string
  name?: string
  password?: string
}

export const usersApi = {
  /**
   * Get all users
   */
  getAll: () =>
    apiClient.get<ApiResponse<User[]>>('/api/users'),

  /**
   * Get user by ID
   */
  getById: (id: number) =>
    apiClient.get<ApiResponse<User>>(`/api/users/${id}`),

  /**
   * Create new user
   */
  create: (data: CreateUserDto) =>
    apiClient.post<ApiResponse<User>>('/api/users', data),

  /**
   * Update user
   */
  update: (id: number, data: UpdateUserDto) =>
    apiClient.patch<ApiResponse<User>>(`/api/users/${id}`, data),

  /**
   * Delete user
   */
  delete: (id: number) =>
    apiClient.delete<ApiResponse<void>>(`/api/users/${id}`),

  /**
   * Search users with query params
   */
  search: (query: string, page: number = 1) =>
    apiClient.get<ApiResponse<User[]>>('/api/users/search', {
      params: { q: query, page },
    }),
}
```

## Step 6: React Query Integration

Create `src/lib/api/hooks/useUsers.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usersApi } from '../services/users'
import type { CreateUserDto, UpdateUserDto } from '../services/users'

/**
 * Query keys for users
 */
export const userKeys = {
  all: ['users'] as const,
  lists: () => [...userKeys.all, 'list'] as const,
  list: (filters: string) => [...userKeys.lists(), { filters }] as const,
  details: () => [...userKeys.all, 'detail'] as const,
  detail: (id: number) => [...userKeys.details(), id] as const,
}

/**
 * Fetch all users
 */
export function useUsers() {
  return useQuery({
    queryKey: userKeys.lists(),
    queryFn: async () => {
      const response = await usersApi.getAll()
      return response.data
    },
  })
}

/**
 * Fetch single user
 */
export function useUser(id: number) {
  return useQuery({
    queryKey: userKeys.detail(id),
    queryFn: async () => {
      const response = await usersApi.getById(id)
      return response.data
    },
    enabled: !!id,
  })
}

/**
 * Create user mutation
 */
export function useCreateUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateUserDto) => usersApi.create(data),
    onSuccess: () => {
      // Invalidate users list to refetch
      queryClient.invalidateQueries({ queryKey: userKeys.lists() })
    },
  })
}

/**
 * Update user mutation
 */
export function useUpdateUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateUserDto }) =>
      usersApi.update(id, data),
    onSuccess: (response, variables) => {
      // Invalidate and refetch user detail
      queryClient.invalidateQueries({ queryKey: userKeys.detail(variables.id) })
      // Invalidate users list
      queryClient.invalidateQueries({ queryKey: userKeys.lists() })
    },
  })
}

/**
 * Delete user mutation
 */
export function useDeleteUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => usersApi.delete(id),
    onSuccess: () => {
      // Invalidate users list to refetch
      queryClient.invalidateQueries({ queryKey: userKeys.lists() })
    },
  })
}

/**
 * Search users with debouncing
 */
export function useSearchUsers(query: string, page: number = 1) {
  return useQuery({
    queryKey: [...userKeys.lists(), 'search', query, page],
    queryFn: async () => {
      const response = await usersApi.search(query, page)
      return response.data
    },
    enabled: query.length > 0,
  })
}
```

## Step 7: Error Handling in Components

Create `src/components/error-boundary.tsx`:

```tsx
import { Component, type ReactNode } from 'react'
import { ApiError, NetworkError, UnauthorizedError } from '~/lib/api/errors'

interface Props {
  children: ReactNode
  fallback?: (error: Error) => ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error) {
    console.error('ErrorBoundary caught:', error)
  }

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error)
      }

      return <DefaultErrorFallback error={this.state.error} />
    }

    return this.props.children
  }
}

function DefaultErrorFallback({ error }: { error: Error }) {
  if (error instanceof UnauthorizedError) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Unauthorized</h1>
          <p className="text-muted-foreground">Please log in to continue</p>
        </div>
      </div>
    )
  }

  if (error instanceof NetworkError) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Network Error</h1>
          <p className="text-muted-foreground">
            Unable to connect to the server. Please check your connection.
          </p>
        </div>
      </div>
    )
  }

  if (error instanceof ApiError) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Error {error.status}</h1>
          <p className="text-muted-foreground">{error.message}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold">Something went wrong</h1>
        <p className="text-muted-foreground">{error.message}</p>
      </div>
    </div>
  )
}
```

## Step 8: Usage in Components

Example component using the API client:

```tsx
import { useUsers, useCreateUser, useDeleteUser } from '~/lib/api/hooks/useUsers'
import { Button } from '~/components/ui/button'
import { useToast } from '~/hooks/use-toast'

export default function UsersPage() {
  const { data: users, isLoading, error } = useUsers()
  const createUser = useCreateUser()
  const deleteUser = useDeleteUser()
  const { toast } = useToast()

  const handleCreate = async () => {
    try {
      await createUser.mutateAsync({
        email: 'new@example.com',
        name: 'New User',
        password: 'password123',
      })
      toast({ title: 'User created successfully' })
    } catch (error) {
      if (error instanceof ValidationError) {
        toast({
          title: 'Validation failed',
          description: Object.values(error.errors).flat().join(', '),
          variant: 'destructive',
        })
      } else {
        toast({
          title: 'Failed to create user',
          variant: 'destructive',
        })
      }
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteUser.mutateAsync(id)
      toast({ title: 'User deleted successfully' })
    } catch (error) {
      toast({
        title: 'Failed to delete user',
        variant: 'destructive',
      })
    }
  }

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>

  return (
    <div>
      <div className="mb-4">
        <Button onClick={handleCreate} disabled={createUser.isPending}>
          {createUser.isPending ? 'Creating...' : 'Create User'}
        </Button>
      </div>

      <div className="space-y-2">
        {users?.map((user) => (
          <div key={user.id} className="flex items-center justify-between">
            <span>{user.name} ({user.email})</span>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => handleDelete(user.id)}
              disabled={deleteUser.isPending}
            >
              Delete
            </Button>
          </div>
        ))}
      </div>
    </div>
  )
}
```

## Step 9: Authentication Integration

Create `src/lib/api/auth.ts`:

```typescript
import { apiClient } from './client'

/**
 * Initialize API client with auth token from storage
 */
export function initializeAuth() {
  const token = localStorage.getItem('auth_token')
  if (token) {
    apiClient.setAuthToken(token)
  }
}

/**
 * Save auth token and update API client
 */
export function setAuthToken(token: string) {
  localStorage.setItem('auth_token', token)
  apiClient.setAuthToken(token)
}

/**
 * Clear auth token and update API client
 */
export function clearAuthToken() {
  localStorage.removeItem('auth_token')
  apiClient.setAuthToken(null)
}
```

Call `initializeAuth()` in your root component or router setup:

```tsx
import { useEffect } from 'react'
import { initializeAuth } from '~/lib/api/auth'

export function App() {
  useEffect(() => {
    initializeAuth()
  }, [])

  return <div>{/* Your app */}</div>
}
```

## Project Structure After Setup

```
your-project/
├── src/
│   ├── lib/
│   │   └── api/
│   │       ├── client.ts           # API client with fetch wrapper
│   │       ├── errors.ts           # Custom error types
│   │       ├── types.ts            # Shared API types
│   │       ├── auth.ts             # Auth token management
│   │       ├── services/           # API service modules
│   │       │   ├── users.ts
│   │       │   └── ...
│   │       └── hooks/              # React Query hooks
│   │           ├── useUsers.ts
│   │           └── ...
│   ├── components/
│   │   └── error-boundary.tsx     # Error handling component
│   └── routes/                     # TanStack routes
├── .env                            # Environment variables
└── vite.config.ts
```

## Advanced Features

### Request Interceptors

Add logging or modify requests globally:

```typescript
// In client.ts, modify the request method:
async request<T = unknown>(
  endpoint: string,
  config: RequestConfig = {}
): Promise<T> {
  // Log all requests in development
  if (import.meta.env.DEV) {
    console.log(`[API] ${config.method || 'GET'} ${endpoint}`, config)
  }

  const { params, headers, ...restConfig } = config

  // Your existing code...
}
```

### Response Caching

Add simple cache layer:

```typescript
private cache = new Map<string, { data: unknown; timestamp: number }>()
private cacheTimeout = 5 * 60 * 1000 // 5 minutes

private getCacheKey(url: string, config: RequestConfig): string {
  return `${url}:${JSON.stringify(config)}`
}

private getFromCache<T>(key: string): T | null {
  const cached = this.cache.get(key)
  if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
    return cached.data as T
  }
  return null
}

private setCache(key: string, data: unknown): void {
  this.cache.set(key, { data, timestamp: Date.now() })
}
```

### Retry Logic

Add automatic retry for failed requests:

```typescript
async requestWithRetry<T>(
  endpoint: string,
  config: RequestConfig = {},
  retries: number = 3
): Promise<T> {
  try {
    return await this.request<T>(endpoint, config)
  } catch (error) {
    if (retries > 0 && error instanceof NetworkError) {
      await new Promise(resolve => setTimeout(resolve, 1000))
      return this.requestWithRetry<T>(endpoint, config, retries - 1)
    }
    throw error
  }
}
```

## Testing

Create `src/lib/api/__tests__/client.test.ts`:

```typescript
import { describe, it, expect, vi } from 'vitest'
import { ApiClient } from '../client'
import { ApiError, NetworkError } from '../errors'

describe('ApiClient', () => {
  it('should make GET request', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: 'test' }),
      headers: new Headers({ 'content-type': 'application/json' }),
    })

    const client = new ApiClient('https://api.example.com')
    const result = await client.get('/test')

    expect(result).toEqual({ data: 'test' })
  })

  it('should throw ApiError on 500', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => ({ message: 'Server error' }),
      headers: new Headers({ 'content-type': 'application/json' }),
    })

    const client = new ApiClient()
    await expect(client.get('/test')).rejects.toThrow(ApiError)
  })

  it('should handle network errors', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network failed'))

    const client = new ApiClient()
    await expect(client.get('/test')).rejects.toThrow(NetworkError)
  })
})
```

## Common Issues

### Issue: CORS errors in development

**Solution:** Configure Vite proxy in `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### Issue: Stale data after mutations

**Solution:** Use proper query invalidation in mutation `onSuccess`:

```typescript
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: userKeys.lists() })
}
```

### Issue: Type errors with generic responses

**Solution:** Explicitly type the response:

```typescript
const response = await apiClient.get<ApiResponse<User[]>>('/api/users')
```

## Notes

- API client is a singleton by default for shared state
- Authentication tokens are automatically added to all requests
- Errors are typed for better error handling
- Works seamlessly with React Query for caching and refetching
- Timeout defaults to 30 seconds per request
- All requests use JSON by default

## Next Steps

After API client setup:
- Create service modules for each API resource
- Add React Query hooks for data fetching
- Implement authentication flows (see `tanstack-client-auth` skill)
- Add optimistic updates for better UX
- Set up error boundaries for graceful error handling

## Resources

- [Fetch API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [React Query Documentation](https://tanstack.com/query/latest)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [Error Handling Best Practices](https://kentcdodds.com/blog/get-a-catch-block-error-message-with-typescript)
