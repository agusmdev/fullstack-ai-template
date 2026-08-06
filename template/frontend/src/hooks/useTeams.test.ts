import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useTeams, pickDefaultTeam } from './useTeams'
import type { TeamsResponse } from '@/types/team'

const apiMock = vi.hoisted(() => ({ get: vi.fn() }))
const authMock = vi.hoisted(() => ({ isAuthenticated: vi.fn() }))

vi.mock('@/lib/api-client', () => ({ api: apiMock }))
vi.mock('@/lib/auth', () => ({
  isAuthenticated: authMock.isAuthenticated,
}))

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function makeWrapper(qc: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: qc }, children)
  }
}

const mockTeams: TeamsResponse = {
  items: [
    { id: 't-1', name: 'Acme', key: 'ACME', issue_sequence: 3, created_at: '', updated_at: '', deleted_at: null },
  ],
  total: 1,
  page: 1,
  size: 50,
  pages: 1,
}

describe('useTeams', () => {
  beforeEach(() => {
    apiMock.get.mockReset()
    authMock.isAuthenticated.mockReset()
  })

  it('fetches GET /teams and returns teams when authenticated', async () => {
    authMock.isAuthenticated.mockReturnValue(true)
    apiMock.get.mockResolvedValue(mockTeams)

    const { result } = renderHook(() => useTeams(), { wrapper: makeWrapper(makeQueryClient()) })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiMock.get).toHaveBeenCalledWith('/teams')
    expect(result.current.data?.items).toHaveLength(1)
  })

  it('is disabled when not authenticated (no fetch fires)', () => {
    authMock.isAuthenticated.mockReturnValue(false)

    const { result } = renderHook(() => useTeams(), { wrapper: makeWrapper(makeQueryClient()) })

    expect(result.current.fetchStatus).toBe('idle')
    expect(apiMock.get).not.toHaveBeenCalled()
  })
})

describe('pickDefaultTeam', () => {
  it('returns the first team when present', () => {
    expect(pickDefaultTeam(mockTeams.items)?.key).toBe('ACME')
  })

  it('returns null for an empty/undefined list', () => {
    expect(pickDefaultTeam(undefined)).toBeNull()
    expect(pickDefaultTeam([])).toBeNull()
  })
})
