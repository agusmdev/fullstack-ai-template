# Frontend Authentication Implementation Guide

## Overview

This document provides implementation guidelines for session-based authentication in the frontend application using localStorage for token storage and Bearer token authentication.

## Authentication Architecture

### Backend API Details

- **Base URL**: `http://localhost:9095/api/v1`
- **Auth Type**: Session-based with Bearer tokens
- **Token Storage**: Frontend localStorage
- **Token Expiration**: 24 hours (configurable via backend)
- **CORS**: Backend is configured to allow `http://localhost:3150`

## Token Storage Strategy

### LocalStorage Implementation

Store the authentication token and user data in localStorage for persistence across page reloads:

```typescript
// auth-storage.ts
interface AuthData {
  token: string;
  expiresAt: string;
  user: {
    id: string;
    email: string;
    created_at: string;
    updated_at: string;
  };
}

const AUTH_STORAGE_KEY = 'auth_data';

export const authStorage = {
  // Store auth data
  set(data: AuthData): void {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(data));
  },

  // Retrieve auth data
  get(): AuthData | null {
    const data = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!data) return null;

    try {
      return JSON.parse(data);
    } catch {
      return null;
    }
  },

  // Clear auth data
  clear(): void {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  },

  // Get just the token
  getToken(): string | null {
    const auth = this.get();
    return auth?.token || null;
  },

  // Check if token is expired
  isExpired(): boolean {
    const auth = this.get();
    if (!auth) return true;

    const expiresAt = new Date(auth.expiresAt);
    return expiresAt < new Date();
  },
};
```

### Why localStorage?

- **Persistence**: Survives page reloads and browser restarts
- **Simple API**: Easy to use with synchronous access
- **Sufficient Security**: For session tokens (not sensitive like passwords)
- **Alternative**: sessionStorage for single-tab sessions or httpOnly cookies for maximum security

## HTTP Client with Authorization Header

### Fetch Wrapper Implementation

Create a fetch wrapper that automatically attaches the Authorization header:

```typescript
// api-client.ts
import { authStorage } from './auth-storage';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:9095';

interface RequestOptions extends RequestInit {
  requiresAuth?: boolean;
}

class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public errors?: Array<{
      loc: string[];
      msg: string;
      type: string;
    }>
  ) {
    super(detail);
    this.name = 'ApiError';
  }
}

export async function apiClient<T = unknown>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { requiresAuth = false, headers = {}, ...fetchOptions } = options;

  // Build request headers
  const requestHeaders: HeadersInit = {
    'Content-Type': 'application/json',
    ...headers,
  };

  // Add Authorization header if required
  if (requiresAuth) {
    const token = authStorage.getToken();

    if (!token) {
      throw new Error('No authentication token found');
    }

    if (authStorage.isExpired()) {
      authStorage.clear();
      throw new Error('Authentication token expired');
    }

    requestHeaders['Authorization'] = `Bearer ${token}`;
  }

  // Make request
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...fetchOptions,
    headers: requestHeaders,
  });

  // Handle errors
  if (!response.ok) {
    let errorDetail = 'An error occurred';
    let errors: ApiError['errors'];

    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorDetail;
      errors = errorData.errors;
    } catch {
      // If error response is not JSON, use status text
      errorDetail = response.statusText;
    }

    throw new ApiError(response.status, errorDetail, errors);
  }

  // Parse response
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}
```

### Usage Examples

```typescript
// Auth API calls
export const authApi = {
  async register(email: string, password: string) {
    return apiClient<{
      user: User;
      token: string;
      session: Session;
    }>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  async login(email: string, password: string) {
    return apiClient<{
      token: string;
      session: Session;
    }>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  async logout() {
    return apiClient('/api/v1/auth/logout', {
      method: 'POST',
      requiresAuth: true,
    });
  },

  async getCurrentUser() {
    return apiClient<User>('/api/v1/auth/me', {
      requiresAuth: true,
    });
  },
};

// Protected API calls (items example)
export const itemsApi = {
  async list() {
    return apiClient<Item[]>('/api/v1/items', {
      requiresAuth: true,
    });
  },

  async create(data: CreateItemDto) {
    return apiClient<Item>('/api/v1/items', {
      method: 'POST',
      body: JSON.stringify(data),
      requiresAuth: true,
    });
  },
};
```

## Authentication Flow Implementation

### 1. Registration Flow

```typescript
// register-page.tsx
async function handleRegister(email: string, password: string) {
  try {
    const response = await authApi.register(email, password);

    // Store auth data
    authStorage.set({
      token: response.token,
      expiresAt: response.session.expires_at,
      user: response.user,
    });

    // Redirect to protected route
    navigate('/items');
  } catch (error) {
    if (error instanceof ApiError) {
      // Handle validation errors
      if (error.status === 422) {
        console.error('Validation errors:', error.errors);
      } else if (error.status === 409) {
        console.error('Email already exists');
      }
    }
    throw error;
  }
}
```

### 2. Login Flow

```typescript
// login-page.tsx
async function handleLogin(email: string, password: string) {
  try {
    const response = await authApi.login(email, password);

    // Store auth data
    authStorage.set({
      token: response.token,
      expiresAt: response.session.expires_at,
      user: await authApi.getCurrentUser(), // Fetch user data
    });

    // Redirect to protected route
    navigate('/items');
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 401) {
        console.error('Invalid credentials');
      }
    }
    throw error;
  }
}
```

### 3. Logout Flow

```typescript
// logout-button.tsx
async function handleLogout() {
  try {
    await authApi.logout();
  } catch (error) {
    console.error('Logout failed:', error);
  } finally {
    // Always clear local auth data
    authStorage.clear();
    navigate('/login');
  }
}
```

### 4. Auth State Management

Using React Context for global auth state:

```typescript
// auth-context.tsx
interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isLoading: boolean;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state on mount
  useEffect(() => {
    const initAuth = async () => {
      const authData = authStorage.get();

      if (!authData || authStorage.isExpired()) {
        authStorage.clear();
        setIsLoading(false);
        return;
      }

      try {
        // Verify token is still valid
        const currentUser = await authApi.getCurrentUser();
        setUser(currentUser);
      } catch {
        // Token invalid, clear storage
        authStorage.clear();
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    const currentUser = await authApi.getCurrentUser();

    authStorage.set({
      token: response.token,
      expiresAt: response.session.expires_at,
      user: currentUser,
    });

    setUser(currentUser);
  };

  const register = async (email: string, password: string) => {
    const response = await authApi.register(email, password);

    authStorage.set({
      token: response.token,
      expiresAt: response.session.expires_at,
      user: response.user,
    });

    setUser(response.user);
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      authStorage.clear();
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

## Protected Routes

### Route Guard Implementation

```typescript
// protected-route.tsx
export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    // Redirect to login, preserving intended destination
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

// Usage in router
<Route
  path="/items"
  element={
    <ProtectedRoute>
      <ItemsPage />
    </ProtectedRoute>
  }
/>
```

## Error Handling

### 401 Unauthorized Response Handler

```typescript
// Enhance apiClient to handle 401
export async function apiClient<T = unknown>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  // ... existing code ...

  if (!response.ok) {
    // Handle 401 Unauthorized
    if (response.status === 401) {
      // Clear invalid auth data
      authStorage.clear();

      // Trigger redirect to login (if in React context)
      window.dispatchEvent(new CustomEvent('auth:unauthorized'));
    }

    // ... rest of error handling ...
  }

  // ... rest of function ...
}

// In AuthProvider or root component
useEffect(() => {
  const handleUnauthorized = () => {
    authStorage.clear();
    setUser(null);
    navigate('/login');
  };

  window.addEventListener('auth:unauthorized', handleUnauthorized);
  return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
}, []);
```

## React Query Integration

### Auth Hooks with React Query

```typescript
// use-auth-query.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

export function useCurrentUser() {
  return useQuery({
    queryKey: ['auth', 'me'],
    queryFn: () => authApi.getCurrentUser(),
    enabled: !!authStorage.getToken(),
    retry: false,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authApi.login(email, password),
    onSuccess: async (response) => {
      const user = await authApi.getCurrentUser();

      authStorage.set({
        token: response.token,
        expiresAt: response.session.expires_at,
        user,
      });

      // Invalidate auth queries
      queryClient.invalidateQueries({ queryKey: ['auth'] });
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => authApi.logout(),
    onSettled: () => {
      authStorage.clear();
      queryClient.clear();
    },
  });
}
```

## Security Considerations

### Best Practices

1. **Token Expiration Handling**
   - Check expiration before each request
   - Clear expired tokens automatically
   - Redirect to login on expiration

2. **XSS Protection**
   - Sanitize user input
   - Use Content Security Policy headers
   - Avoid storing sensitive data in localStorage

3. **CSRF Protection**
   - Backend uses session-based auth (not cookies)
   - Bearer tokens are not vulnerable to CSRF
   - Still validate origin on backend

4. **Token Refresh** (Future Enhancement)
   - Current implementation: 24-hour tokens
   - Consider adding refresh token endpoint for longer sessions

### Alternative: httpOnly Cookies

For maximum security, consider moving to httpOnly cookies:

**Pros:**
- Not accessible to JavaScript (XSS protection)
- Automatically sent with requests
- More secure storage

**Cons:**
- Requires CORS credentials setup
- More complex logout (requires backend endpoint)
- Mobile app integration is harder

**Backend changes required:**
- Set `Set-Cookie` header on login
- Use `Secure; HttpOnly; SameSite=Strict` flags
- Remove Authorization header requirement

## Environment Variables

```env
# .env
VITE_API_URL=http://localhost:9095
```

## Testing Authentication

### Unit Tests

```typescript
// auth-storage.test.ts
describe('authStorage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('stores and retrieves auth data', () => {
    const data = {
      token: 'test-token',
      expiresAt: new Date(Date.now() + 86400000).toISOString(),
      user: { id: '1', email: 'test@example.com' },
    };

    authStorage.set(data);
    expect(authStorage.get()).toEqual(data);
  });

  it('detects expired tokens', () => {
    const data = {
      token: 'test-token',
      expiresAt: new Date(Date.now() - 1000).toISOString(),
      user: { id: '1', email: 'test@example.com' },
    };

    authStorage.set(data);
    expect(authStorage.isExpired()).toBe(true);
  });
});
```

### Integration Tests (Playwright)

```typescript
// auth.spec.ts
test('login flow persists session', async ({ page }) => {
  await page.goto('/login');

  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');

  // Should redirect to protected route
  await expect(page).toHaveURL('/items');

  // Reload page - session should persist
  await page.reload();
  await expect(page).toHaveURL('/items');

  // Check localStorage
  const authData = await page.evaluate(() =>
    localStorage.getItem('auth_data')
  );
  expect(authData).toBeTruthy();
});

test('logout clears session', async ({ page }) => {
  // Login first
  await loginHelper(page, 'test@example.com', 'password123');

  // Logout
  await page.click('button[aria-label="Logout"]');

  // Should redirect to login
  await expect(page).toHaveURL('/login');

  // localStorage should be empty
  const authData = await page.evaluate(() =>
    localStorage.getItem('auth_data')
  );
  expect(authData).toBeNull();
});
```

## TypeScript Types

```typescript
// types/auth.ts
export interface User {
  id: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: string;
  user_id: string;
  token: string;
  expires_at: string;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  session: Session;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface RegisterResponse {
  user: User;
  token: string;
  session: Session;
}

export interface ErrorResponse {
  detail: string;
  errors?: Array<{
    loc: string[];
    msg: string;
    type: string;
  }>;
}
```

## Implementation Checklist

- [ ] Create `auth-storage.ts` with localStorage utilities
- [ ] Create `api-client.ts` with Authorization header injection
- [ ] Create `auth-api.ts` with login/register/logout/me endpoints
- [ ] Create `AuthContext` and `AuthProvider` for global state
- [ ] Create `ProtectedRoute` component for route guards
- [ ] Add 401 error handling with automatic logout
- [ ] Add token expiration checking
- [ ] Integrate with React Query for auth mutations
- [ ] Add login/register/logout UI components
- [ ] Write unit tests for auth utilities
- [ ] Write integration tests for auth flows
- [ ] Document environment variables
- [ ] Add error messages for common auth failures

## References

- Backend Auth Implementation: `template/backend/src/app/api/v1/auth/`
- Backend Auth Models: `template/backend/src/app/models/`
- Project README: `template/README.md`
- Epic 5 Tasks: Lines 587-596 in `.sisyphus/plans/ai-fullstack-ready-template.md`
