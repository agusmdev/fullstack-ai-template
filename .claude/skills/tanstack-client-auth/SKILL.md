---
name: tanstack-client-auth
description: Token-based authentication for TanStack Client (SPA) apps including login/logout, protected routes, auth context, token storage, and route guards. SHARED skill for both TanStack Start (client-only mode) and TanStack Router.
---

# TanStack Client Authentication

## Overview

This skill covers implementing token-based authentication in TanStack Router (SPA) and TanStack Start (client-only mode) applications. It includes token storage, authentication context, protected routes, route guards, and integration with API clients.

**Important:** This skill is for client-side authentication. For server-side session-based auth in TanStack Start with SSR, use `tanstack-start-auth` instead.

## When to Use This Skill

Use this skill when:
- Building a TanStack Router SPA with external API backend
- Using TanStack Start in client-only mode (`defaultSsr: false`)
- Implementing JWT or token-based authentication
- Need to protect routes behind authentication
- Managing auth state client-side

## Prerequisites

- TanStack Router or TanStack Start project set up
- API backend with authentication endpoints
- Basic understanding of JWT tokens

## Architecture Overview

```
Auth Flow:
1. User submits credentials → POST /api/auth/login
2. Backend returns token → Store in localStorage/sessionStorage
3. Add token to API requests → Authorization: Bearer {token}
4. Check auth state → Redirect to /login if needed
5. Logout → Clear token → Redirect to /login

Components:
- AuthContext: Global auth state management
- AuthProvider: Wraps app with auth context
- useAuth: Hook to access auth state
- Protected Routes: Components that require authentication
- Route Guards: beforeLoad checks for auth
- Token Storage: localStorage/sessionStorage utilities
```

## Step 1: Create Auth Types

Create `src/lib/auth/types.ts`:

```typescript
// src/lib/auth/types.ts
export interface User {
  id: string
  email: string
  display_name: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

export interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  register: (email: string, password: string, displayName: string) => Promise<void>
  refreshUser: () => Promise<void>
}

export interface LoginResponse {
  token: string
  user: User
}

export interface RegisterRequest {
  email: string
  password: string
  display_name: string
}
```

## Step 2: Create Token Storage Utilities

Create `src/lib/auth/storage.ts`:

```typescript
// src/lib/auth/storage.ts
const TOKEN_KEY = 'auth_token'
const USER_KEY = 'auth_user'

export const tokenStorage = {
  /**
   * Get stored authentication token
   */
  getToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(TOKEN_KEY)
  },

  /**
   * Save authentication token
   */
  setToken(token: string): void {
    if (typeof window === 'undefined') return
    localStorage.setItem(TOKEN_KEY, token)
  },

  /**
   * Remove authentication token
   */
  removeToken(): void {
    if (typeof window === 'undefined') return
    localStorage.removeItem(TOKEN_KEY)
  },

  /**
   * Get stored user data
   */
  getUser(): User | null {
    if (typeof window === 'undefined') return null
    const userJson = localStorage.getItem(USER_KEY)
    if (!userJson) return null

    try {
      return JSON.parse(userJson) as User
    } catch {
      return null
    }
  },

  /**
   * Save user data
   */
  setUser(user: User): void {
    if (typeof window === 'undefined') return
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  },

  /**
   * Remove user data
   */
  removeUser(): void {
    if (typeof window === 'undefined') return
    localStorage.removeItem(USER_KEY)
  },

  /**
   * Clear all auth data
   */
  clear(): void {
    this.removeToken()
    this.removeUser()
  },
}

// Alternative: sessionStorage version (expires on tab close)
export const sessionTokenStorage = {
  getToken(): string | null {
    if (typeof window === 'undefined') return null
    return sessionStorage.getItem(TOKEN_KEY)
  },

  setToken(token: string): void {
    if (typeof window === 'undefined') return
    sessionStorage.setItem(TOKEN_KEY, token)
  },

  removeToken(): void {
    if (typeof window === 'undefined') return
    sessionStorage.removeItem(TOKEN_KEY)
  },

  getUser(): User | null {
    if (typeof window === 'undefined') return null
    const userJson = sessionStorage.getItem(USER_KEY)
    if (!userJson) return null

    try {
      return JSON.parse(userJson) as User
    } catch {
      return null
    }
  },

  setUser(user: User): void {
    if (typeof window === 'undefined') return
    sessionStorage.setItem(USER_KEY, JSON.stringify(user))
  },

  removeUser(): void {
    if (typeof window === 'undefined') return
    sessionStorage.removeItem(USER_KEY)
  },

  clear(): void {
    this.removeToken()
    this.removeUser()
  },
}
```

## Step 3: Create Auth API Client

Create `src/lib/auth/api.ts`:

```typescript
// src/lib/auth/api.ts
import { apiClient } from '~/lib/api/client'
import type { LoginResponse, RegisterRequest, User } from './types'

export const authApi = {
  /**
   * Login with email and password
   */
  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/auth/login', {
      email,
      password,
    })
    return response.data
  },

  /**
   * Register new user
   */
  async register(data: RegisterRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/auth/register', data)
    return response.data
  },

  /**
   * Get current authenticated user
   */
  async me(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me')
    return response.data
  },

  /**
   * Logout (optional - call backend logout endpoint)
   */
  async logout(): Promise<void> {
    await apiClient.post('/auth/logout')
  },
}
```

## Step 4: Create Auth Context

Create `src/lib/auth/context.tsx`:

```typescript
// src/lib/auth/context.tsx
import { createContext, useContext, useEffect, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { authApi } from './api'
import { tokenStorage } from './storage'
import type { AuthContextValue, User } from './types'

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Initialize auth state from storage on mount
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = tokenStorage.getToken()
      const storedUser = tokenStorage.getUser()

      if (storedToken && storedUser) {
        setToken(storedToken)
        setUser(storedUser)

        // Optionally verify token is still valid
        try {
          const currentUser = await authApi.me()
          setUser(currentUser)
          tokenStorage.setUser(currentUser)
        } catch (error) {
          // Token invalid, clear storage
          tokenStorage.clear()
          setToken(null)
          setUser(null)
        }
      }

      setIsLoading(false)
    }

    initAuth()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      const response = await authApi.login(email, password)

      // Store token and user
      tokenStorage.setToken(response.token)
      tokenStorage.setUser(response.user)

      setToken(response.token)
      setUser(response.user)

      // Redirect to dashboard or intended destination
      navigate({ to: '/dashboard' })
    } catch (error) {
      // Re-throw for component to handle
      throw error
    }
  }

  const register = async (
    email: string,
    password: string,
    displayName: string
  ) => {
    try {
      const response = await authApi.register({
        email,
        password,
        display_name: displayName,
      })

      // Store token and user
      tokenStorage.setToken(response.token)
      tokenStorage.setUser(response.user)

      setToken(response.token)
      setUser(response.user)

      // Redirect to dashboard
      navigate({ to: '/dashboard' })
    } catch (error) {
      throw error
    }
  }

  const logout = () => {
    // Clear storage
    tokenStorage.clear()

    // Clear state
    setToken(null)
    setUser(null)

    // Optionally call backend logout
    authApi.logout().catch(() => {
      // Ignore errors on logout
    })

    // Redirect to login
    navigate({ to: '/login' })
  }

  const refreshUser = async () => {
    if (!token) return

    try {
      const currentUser = await authApi.me()
      setUser(currentUser)
      tokenStorage.setUser(currentUser)
    } catch (error) {
      // Token invalid, logout
      logout()
    }
  }

  const value: AuthContextValue = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    isLoading,
    login,
    logout,
    register,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
```

## Step 5: Wrap App with AuthProvider

Update `src/routes/__root.tsx`:

```tsx
// src/routes/__root.tsx
import { createRootRoute, Outlet } from '@tanstack/react-router'
import { AuthProvider } from '~/lib/auth/context'

export const Route = createRootRoute({
  component: () => (
    <AuthProvider>
      <Outlet />
    </AuthProvider>
  ),
})
```

## Step 6: Create Protected Route Component

Create `src/components/auth/protected-route.tsx`:

```tsx
// src/components/auth/protected-route.tsx
import { Navigate } from '@tanstack/react-router'
import { useAuth } from '~/lib/auth/context'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="mt-2 text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />
  }

  return <>{children}</>
}
```

## Step 7: Implement Route Guards with beforeLoad

For better performance, use `beforeLoad` to check auth before loading route:

```typescript
// src/routes/dashboard.tsx
import { createFileRoute, redirect } from '@tanstack/react-router'
import { tokenStorage } from '~/lib/auth/storage'

export const Route = createFileRoute('/dashboard')({
  // Check auth before loading this route
  beforeLoad: async ({ location }) => {
    const token = tokenStorage.getToken()

    if (!token) {
      throw redirect({
        to: '/login',
        search: {
          // Save intended destination for redirect after login
          redirect: location.href,
        },
      })
    }
  },
  component: DashboardComponent,
})

function DashboardComponent() {
  const { user } = useAuth()

  return (
    <div>
      <h1>Dashboard</h1>
      <p>Welcome, {user?.display_name}!</p>
    </div>
  )
}
```

## Step 8: Create Login Page

Create `src/routes/login.tsx`:

```tsx
// src/routes/login.tsx
import { createFileRoute, useNavigate, useSearch } from '@tanstack/react-router'
import { useState } from 'react'
import { useAuth } from '~/lib/auth/context'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'

export const Route = createFileRoute('/login')({
  component: LoginPage,
})

function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const search = useSearch({ from: '/login' })

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // Redirect if already authenticated
  if (isAuthenticated) {
    const redirectTo = (search as any)?.redirect || '/dashboard'
    navigate({ to: redirectTo })
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      await login(email, password)
      // Navigation handled by AuthContext
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md space-y-6 rounded-lg border p-8">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-bold">Sign In</h1>
          <p className="text-muted-foreground">
            Enter your credentials to access your account
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          Don't have an account?{' '}
          <a href="/register" className="text-primary hover:underline">
            Sign up
          </a>
        </p>
      </div>
    </div>
  )
}
```

## Step 9: Integrate Auth Token with API Client

Update your API client to include auth token in requests:

```typescript
// src/lib/api/client.ts
import axios from 'axios'
import { tokenStorage } from '~/lib/auth/storage'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: Add auth token to all requests
apiClient.interceptors.request.use(
  (config) => {
    const token = tokenStorage.getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor: Handle 401 Unauthorized
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      tokenStorage.clear()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

## Step 10: Create Logout Component

Create `src/components/auth/logout-button.tsx`:

```tsx
// src/components/auth/logout-button.tsx
import { useAuth } from '~/lib/auth/context'
import { Button } from '~/components/ui/button'

export function LogoutButton() {
  const { logout, user } = useAuth()

  return (
    <div className="flex items-center gap-4">
      <span className="text-sm text-muted-foreground">{user?.email}</span>
      <Button variant="outline" onClick={logout}>
        Logout
      </Button>
    </div>
  )
}
```

## Advanced Patterns

### Pattern 1: Role-Based Access Control

```typescript
// src/lib/auth/types.ts
export interface User {
  id: string
  email: string
  display_name: string
  role: 'admin' | 'user' | 'guest'
}

// src/lib/auth/guards.ts
import { tokenStorage } from './storage'

export function requireRole(role: 'admin' | 'user') {
  return () => {
    const user = tokenStorage.getUser()

    if (!user) {
      throw redirect({ to: '/login' })
    }

    if (user.role !== role && user.role !== 'admin') {
      throw redirect({ to: '/unauthorized' })
    }
  }
}

// Usage in route
export const Route = createFileRoute('/admin')({
  beforeLoad: requireRole('admin'),
  component: AdminPage,
})
```

### Pattern 2: Refresh Token Handling

```typescript
// src/lib/auth/storage.ts
const REFRESH_TOKEN_KEY = 'refresh_token'

export const tokenStorage = {
  // ... existing methods

  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  },

  setRefreshToken(token: string): void {
    if (typeof window === 'undefined') return
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
  },

  removeRefreshToken(): void {
    if (typeof window === 'undefined') return
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

// src/lib/api/client.ts
let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((callback) => callback(token))
  refreshSubscribers = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Wait for token refresh
        return new Promise((resolve) => {
          refreshSubscribers.push((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(apiClient(originalRequest))
          })
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refreshToken = tokenStorage.getRefreshToken()
        if (!refreshToken) {
          throw new Error('No refresh token')
        }

        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        })

        const { token } = response.data
        tokenStorage.setToken(token)

        onTokenRefreshed(token)
        isRefreshing = false

        originalRequest.headers.Authorization = `Bearer ${token}`
        return apiClient(originalRequest)
      } catch (refreshError) {
        // Refresh failed, logout
        tokenStorage.clear()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)
```

### Pattern 3: Remember Me Functionality

```typescript
// src/lib/auth/context.tsx
const login = async (email: string, password: string, rememberMe: boolean = false) => {
  try {
    const response = await authApi.login(email, password)

    const storage = rememberMe ? tokenStorage : sessionTokenStorage
    storage.setToken(response.token)
    storage.setUser(response.user)

    setToken(response.token)
    setUser(response.user)

    navigate({ to: '/dashboard' })
  } catch (error) {
    throw error
  }
}
```

### Pattern 4: Auth Loading Skeleton

```tsx
// src/components/auth/auth-guard.tsx
import { Outlet } from '@tanstack/react-router'
import { useAuth } from '~/lib/auth/context'

export function AuthGuard() {
  const { isLoading } = useAuth()

  if (isLoading) {
    return <AuthLoadingSkeleton />
  }

  return <Outlet />
}

function AuthLoadingSkeleton() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="space-y-4">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        <p className="text-sm text-muted-foreground">Authenticating...</p>
      </div>
    </div>
  )
}
```

## Security Best Practices

1. **Never store sensitive data in localStorage**
   - Only store tokens, not passwords
   - Consider using httpOnly cookies for production

2. **Always use HTTPS in production**
   - Tokens sent over HTTP can be intercepted

3. **Implement token expiration**
   - Short-lived access tokens (15 mins - 1 hour)
   - Long-lived refresh tokens (days - weeks)

4. **Validate tokens on every request**
   - Backend should verify token signature
   - Check expiration time

5. **Clear tokens on logout**
   - Remove from storage
   - Invalidate on backend

6. **Handle token theft**
   - Implement token rotation
   - Monitor for suspicious activity
   - Add device/IP tracking

## Verification

Test your authentication implementation:

1. **Login flow:**
   ```bash
   # Start dev server
   bun run dev

   # Navigate to /login
   # Submit credentials
   # Verify redirect to /dashboard
   # Check localStorage for token
   ```

2. **Protected routes:**
   ```bash
   # Without auth: Navigate to /dashboard
   # Should redirect to /login

   # With auth: Navigate to /dashboard
   # Should show dashboard content
   ```

3. **Logout:**
   ```bash
   # Click logout button
   # Verify redirect to /login
   # Check localStorage (should be empty)
   ```

4. **Token persistence:**
   ```bash
   # Login
   # Refresh page
   # Should remain authenticated
   ```

5. **API integration:**
   ```bash
   # Check Network tab in DevTools
   # Verify Authorization header in requests
   ```

## Troubleshooting

### Issue: "useAuth must be used within AuthProvider"

**Cause:** Using `useAuth()` outside of `<AuthProvider>`.

**Solution:** Ensure `__root.tsx` wraps app with `<AuthProvider>`:
```tsx
export const Route = createRootRoute({
  component: () => (
    <AuthProvider>
      <Outlet />
    </AuthProvider>
  ),
})
```

### Issue: Infinite redirect loop

**Cause:** Protected route redirects to login, which redirects back.

**Solution:** Exclude `/login` from authentication checks:
```typescript
export const Route = createFileRoute('/login')({
  beforeLoad: ({ location }) => {
    const token = tokenStorage.getToken()
    if (token) {
      throw redirect({ to: '/dashboard' })
    }
  },
})
```

### Issue: Token persists after logout

**Cause:** Not clearing all storage.

**Solution:** Use `tokenStorage.clear()` in logout function.

### Issue: 401 errors after page refresh

**Cause:** Token not loaded from storage on mount.

**Solution:** Verify `useEffect` in `AuthProvider` loads token from storage.

## Project Structure

```
src/
├── routes/
│   ├── __root.tsx              # AuthProvider wrapper
│   ├── login.tsx               # Login page
│   ├── register.tsx            # Registration page
│   └── dashboard.tsx           # Protected route
├── lib/
│   ├── auth/
│   │   ├── types.ts            # Auth type definitions
│   │   ├── context.tsx         # AuthContext and AuthProvider
│   │   ├── storage.ts          # Token storage utilities
│   │   ├── api.ts              # Auth API client
│   │   └── guards.ts           # Route guard utilities (optional)
│   └── api/
│       └── client.ts           # Axios client with interceptors
└── components/
    ├── auth/
    │   ├── protected-route.tsx # Protected route component
    │   └── logout-button.tsx   # Logout button
    └── ui/                     # shadcn/ui components
```

## Notes

- This skill covers client-side token-based authentication
- For server-side session auth in TanStack Start (SSR), use `tanstack-start-auth` skill
- Tokens are stored in localStorage by default (consider security implications)
- Always use HTTPS in production to protect tokens
- Implement refresh token rotation for enhanced security
- Consider using httpOnly cookies for production applications

## Next Steps

After implementing authentication:
- Set up React Query with authenticated requests (see `tanstack-react-query-setup`)
- Build registration and password reset flows
- Add multi-factor authentication (MFA)
- Implement OAuth/SSO providers
- Add user profile management
- Set up role-based access control (RBAC)

## Resources

- [TanStack Router Authentication Guide](https://tanstack.com/router/latest/docs/guide/authenticated-routes)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
