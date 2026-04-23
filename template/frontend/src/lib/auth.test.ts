import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  AUTH_TOKEN_KEY,
  getAuthToken,
  setAuthToken,
  clearAuthToken,
  isAuthenticated,
  subscribeToAuthChanges,
} from './auth'

describe('auth utilities', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  describe('getAuthToken', () => {
    it('returns null when no token stored', () => {
      expect(getAuthToken()).toBeNull()
    })

    it('returns the stored token', () => {
      localStorage.setItem(AUTH_TOKEN_KEY, 'test-token')
      expect(getAuthToken()).toBe('test-token')
    })
  })

  describe('setAuthToken', () => {
    it('stores the token in localStorage', () => {
      setAuthToken('my-token')
      expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBe('my-token')
    })

    it('notifies auth change listeners', () => {
      const listener = vi.fn()
      const unsub = subscribeToAuthChanges(listener)
      setAuthToken('new-token')
      expect(listener).toHaveBeenCalledTimes(1)
      unsub()
    })
  })

  describe('clearAuthToken', () => {
    it('removes the token from localStorage', () => {
      localStorage.setItem(AUTH_TOKEN_KEY, 'to-clear')
      clearAuthToken()
      expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBeNull()
    })

    it('notifies auth change listeners on clear', () => {
      const listener = vi.fn()
      const unsub = subscribeToAuthChanges(listener)
      clearAuthToken()
      expect(listener).toHaveBeenCalledTimes(1)
      unsub()
    })
  })

  describe('isAuthenticated', () => {
    it('returns false when no token', () => {
      expect(isAuthenticated()).toBe(false)
    })

    it('returns true when token is present', () => {
      setAuthToken('valid-token')
      expect(isAuthenticated()).toBe(true)
    })

    it('returns false after token is cleared', () => {
      setAuthToken('valid-token')
      clearAuthToken()
      expect(isAuthenticated()).toBe(false)
    })
  })

  describe('subscribeToAuthChanges', () => {
    it('returns an unsubscribe function', () => {
      const listener = vi.fn()
      const unsub = subscribeToAuthChanges(listener)
      expect(typeof unsub).toBe('function')
      unsub()
    })

    it('stops notifying after unsubscribe', () => {
      const listener = vi.fn()
      const unsub = subscribeToAuthChanges(listener)
      unsub()
      setAuthToken('token')
      expect(listener).not.toHaveBeenCalled()
    })

    it('notifies multiple listeners', () => {
      const l1 = vi.fn()
      const l2 = vi.fn()
      const u1 = subscribeToAuthChanges(l1)
      const u2 = subscribeToAuthChanges(l2)
      setAuthToken('tok')
      expect(l1).toHaveBeenCalledTimes(1)
      expect(l2).toHaveBeenCalledTimes(1)
      u1()
      u2()
    })
  })
})
