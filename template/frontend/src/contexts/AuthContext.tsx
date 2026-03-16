import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
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

/**
 * Creates the auth change handler used in AuthProvider's subscription.
 * Exported for unit testing without needing to mount the React component tree.
 */
export function createAuthChangeHandler(
  setTokenState: (token: string | null) => void,
  queryClient: QueryClient,
  navigate: (opts: { to: string }) => void,
) {
  return () => {
    const currentToken = getAuthToken()
    setTokenState(currentToken)
    if (currentToken === null) {
      queryClient.clear()
      navigate({ to: '/login' })
    }
  }
}

export function AuthProvider({ children, queryClient }: AuthProviderProps) {
  const router = useRouter()
  const [token, setTokenState] = useState<string | null>(() => {
    return getAuthToken()
  })

  // Subscribe to auth changes from external sources (like api-client clearing token on 401)
  useEffect(() => {
    return subscribeToAuthChanges(
      createAuthChangeHandler(setTokenState, queryClient, router.navigate)
    )
  }, [queryClient, router])

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
    } finally {
      // Always clear local auth state
      clearAuthToken()
      setTokenState(null)
      queryClient.clear()
    }
  }, [queryClient])

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
