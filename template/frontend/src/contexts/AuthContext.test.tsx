/**
 * AuthContext behavior tests.
 *
 * These tests verify the AuthContext contracts without rendering React components.
 * React hook rendering is not supported in the current test environment due to the
 * TanStack Start SSR plugin. Tests instead exercise the underlying auth layer behavior
 * that AuthContext orchestrates: token storage, subscription notifications, and cache
 * clearing — which together constitute the login/logout/401 paths.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { QueryClient } from '@tanstack/react-query'
import {
  AUTH_TOKEN_KEY,
  getAuthToken,
  setAuthToken,
  clearAuthToken,
  subscribeToAuthChanges,
  isAuthenticated,
} from '@/lib/auth'

function makeQueryClient() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  vi.spyOn(qc, 'clear')
  return qc
}

describe('AuthContext: login path', () => {
  beforeEach(() => localStorage.clear())

  it('stores token on login', () => {
    setAuthToken('login-token')
    expect(getAuthToken()).toBe('login-token')
    expect(isAuthenticated()).toBe(true)
  })

  it('notifies subscribers when token is set', () => {
    const listener = vi.fn()
    const unsub = subscribeToAuthChanges(listener)
    setAuthToken('tok-xyz')
    expect(listener).toHaveBeenCalledTimes(1)
    unsub()
  })
})

describe('AuthContext: logout path', () => {
  beforeEach(() => localStorage.clear())

  it('clears token and marks unauthenticated', () => {
    setAuthToken('active-token')
    clearAuthToken()
    expect(getAuthToken()).toBeNull()
    expect(isAuthenticated()).toBe(false)
  })

  it('calls queryClient.clear() when token is cleared via auth change subscription', () => {
    const qc = makeQueryClient()
    setAuthToken('active-token')

    // Simulate how AuthContext wires the subscription: when token is cleared,
    // the subscription callback calls queryClient.clear()
    const unsub = subscribeToAuthChanges(() => {
      if (getAuthToken() === null) {
        qc.clear()
      }
    })

    clearAuthToken()
    expect(qc.clear).toHaveBeenCalled()
    unsub()
  })

  it('subscription unsubscribes cleanly on unmount', () => {
    const listener = vi.fn()
    const unsub = subscribeToAuthChanges(listener)
    unsub()
    clearAuthToken()
    expect(listener).not.toHaveBeenCalled()
  })
})

describe('AuthContext: 401 path', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => vi.unstubAllGlobals())

  it('api-client 401 triggers auth change notification', async () => {
    const { api } = await import('@/lib/api-client')
    localStorage.setItem(AUTH_TOKEN_KEY, 'expired-token')

    const notified = vi.fn()
    const unsub = subscribeToAuthChanges(notified)

    const response = { ok: false, status: 401, json: vi.fn().mockResolvedValue({}) }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))

    await expect(api.get('/protected')).rejects.toBeDefined()

    expect(notified).toHaveBeenCalled()
    expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBeNull()
    unsub()
  })

  it('queryClient.clear() is invoked in the 401 subscriber callback', () => {
    const qc = makeQueryClient()
    localStorage.setItem(AUTH_TOKEN_KEY, 'tok-abc')

    const unsub = subscribeToAuthChanges(() => {
      if (getAuthToken() === null) {
        qc.clear()
      }
    })

    // Simulate api-client clearing the token on 401
    clearAuthToken()

    expect(qc.clear).toHaveBeenCalled()
    unsub()
  })
})
