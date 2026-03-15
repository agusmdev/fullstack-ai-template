import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import type { QueryClient } from '@tanstack/react-query'
import { getAuthToken, setAuthToken, clearAuthToken, subscribeToAuthChanges } from '@/lib/auth'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import type { AuthSessionResponse } from '@/types/auth'

interface AuthContextValue {
  isAuthenticated: boolean
  token: string | null
  login: (response: AuthSessionResponse) => void
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

interface AuthProviderProps {
  children: React.ReactNode
  queryClient: QueryClient
}

export function AuthProvider({ children, queryClient }: AuthProviderProps) {
  const [token, setTokenState] = useState<string | null>(() => {
    return getAuthToken()
  })

  // Subscribe to auth changes from external sources (like api-client clearing token on 401)
  useEffect(() => {
    const unsubscribe = subscribeToAuthChanges(() => {
      const currentToken = getAuthToken()
      setTokenState(currentToken)

      if (currentToken === null) {
        queryClient.clear()
      }
    })

    return unsubscribe
  }, [queryClient])

  const login = useCallback((response: AuthSessionResponse) => {
    if (!response.id) {
      throw new Error('No session token returned from server')
    }
    setAuthToken(response.id)
    setTokenState(response.id)
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
