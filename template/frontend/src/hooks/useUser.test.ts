import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useUser } from './useUser'
import type { User } from '@/types/user'

const apiMock = vi.hoisted(() => ({ get: vi.fn() }))
const authMock = vi.hoisted(() => ({ isAuthenticated: vi.fn() }))

vi.mock('@/lib/api-client', () => ({ api: apiMock }))
vi.mock('@/lib/auth', () => ({
  isAuthenticated: authMock.isAuthenticated,
}))

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
}

function makeWrapper(qc: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: qc }, children)
  }
}

const mockUser: User = {
  id: 'u-1',
  email: 'jane@example.com',
  display_name: 'Jane',
  email_verified_at: null,
  is_email_verified: false,
}

describe('useUser', () => {
  beforeEach(() => {
    apiMock.get.mockReset()
    authMock.isAuthenticated.mockReset()
  })

  it('fetches GET /users/me and returns the user when authenticated', async () => {
    authMock.isAuthenticated.mockReturnValue(true)
    apiMock.get.mockResolvedValue(mockUser)

    const { result } = renderHook(() => useUser(), {
      wrapper: makeWrapper(makeQueryClient()),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiMock.get).toHaveBeenCalledWith('/users/me')
    expect(result.current.data).toEqual(mockUser)
  })

  it('is disabled when not authenticated (no fetch fires)', () => {
    authMock.isAuthenticated.mockReturnValue(false)

    const { result } = renderHook(() => useUser(), {
      wrapper: makeWrapper(makeQueryClient()),
    })

    expect(result.current.fetchStatus).toBe('idle')
    expect(apiMock.get).not.toHaveBeenCalled()
  })
})
