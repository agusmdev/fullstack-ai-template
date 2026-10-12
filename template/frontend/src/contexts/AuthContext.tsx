import React, {
  createContext,
  useContext,
  useEffect,
  useCallback,
  useSyncExternalStore,
} from 'react'
import { useRouter } from '@tanstack/react-router'
import type { QueryClient } from '@tanstack/react-query'
import { getAuthToken, setAuthToken, clearAuthToken, subscribeToAuthChanges } from '@/lib/auth'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'

interface AuthContextValue {
  isAuthenticated: boolean
  token: string | null
  /** Sync — sets the auth token and updates state. Do not await. */
  login: (token: string) => void
  /** Async — calls the backend logout endpoint then clears local state. Must be awaited. */
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

interface AuthProviderProps {
  children: React.ReactNode
  queryClient: QueryClient
}

// The token lives in localStorage, which the server cannot read. The server
// renders "signed out"; after hydration the client switches to the stored
// token without a hydration mismatch.
const getServerToken = () => null

export function AuthProvider({ children, queryClient }: AuthProviderProps) {
  const router = useRouter()
  const token = useSyncExternalStore(subscribeToAuthChanges, getAuthToken, getServerToken)

  // When the token goes away (logout, or the API client dropped a rejected
  // session), drop the signed-in user's cached data. Pages in routes/_authed/
  // then send the user to /login by themselves.
  useEffect(() => {
    return subscribeToAuthChanges(() => {
      if (getAuthToken() === null) queryClient.clear()
    })
  }, [queryClient])

  const login = useCallback((token: string) => {
    setAuthToken(token)
  }, [])

  const logout = useCallback(async () => {
    // Call backend logout endpoint to invalidate session
    try {
      const token = getAuthToken()
      if (token) {
        await api.post(API.AUTH.LOGOUT, {})
      }
    } catch {
      // Ignore errors - still clear local auth state even if backend call fails
    }
    // Leave the page first, so a protected page does not redirect to
    // /login?redirect=<itself> when the token goes away.
    await router.navigate({ to: '/login' })
    clearAuthToken()
  }, [router])

  const isAuthenticated = token !== null

  return (
    <AuthContext.Provider value={{ isAuthenticated, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
