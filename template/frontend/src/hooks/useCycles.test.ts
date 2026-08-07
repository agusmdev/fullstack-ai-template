import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import {
  useCycles,
  useCycle,
  useCreateCycle,
  useUpdateCycle,
  useDeleteCycle,
  useCycleLookup,
} from './useCycles'
import type { CyclesResponse, Cycle } from '@/types/cycle'

const apiMock = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
}))
const authMock = vi.hoisted(() => ({ isAuthenticated: vi.fn() }))
const toastMock = vi.hoisted(() => ({
  success: vi.fn(),
  error: vi.fn(),
}))

vi.mock('@/lib/api-client', () => ({ api: apiMock }))
vi.mock('@/lib/auth', () => ({
  isAuthenticated: authMock.isAuthenticated,
}))
vi.mock('sonner', () => ({
  toast: toastMock,
}))

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
}
function makeWrapper(qc: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: qc }, children)
  }
}

const mockCycle: Cycle = {
  id: 'c-1',
  team_id: 't-1',
  name: 'Sprint 1',
  starts_at: '2026-08-01',
  ends_at: '2026-08-14',
  completed_at: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

const mockCycles: CyclesResponse = {
  items: [mockCycle],
  total: 1,
  page: 1,
  size: 100,
  pages: 1,
}

describe('useCycles', () => {
  beforeEach(() => {
    apiMock.get.mockReset()
    authMock.isAuthenticated.mockReset()
    toastMock.success.mockReset()
  })

  it('fetches cycles scoped to the team when authenticated', async () => {
    authMock.isAuthenticated.mockReturnValue(true)
    apiMock.get.mockResolvedValue(mockCycles)

    const { result } = renderHook(() => useCycles('t-1'), {
      wrapper: makeWrapper(makeQueryClient()),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiMock.get).toHaveBeenCalledWith(
      expect.stringContaining('/cycles?team_id=t-1'),
    )
    expect(result.current.data?.items).toHaveLength(1)
  })

  it('is disabled without a teamId', () => {
    authMock.isAuthenticated.mockReturnValue(true)
    const { result } = renderHook(() => useCycles(undefined), {
      wrapper: makeWrapper(makeQueryClient()),
    })
    expect(result.current.fetchStatus).toBe('idle')
    expect(apiMock.get).not.toHaveBeenCalled()
  })
})

describe('useCycle', () => {
  beforeEach(() => {
    authMock.isAuthenticated.mockReturnValue(true)
    apiMock.get.mockReset()
  })

  it('fetches a single cycle by id', async () => {
    apiMock.get.mockResolvedValue(mockCycle)
    const { result } = renderHook(() => useCycle('c-1'), {
      wrapper: makeWrapper(makeQueryClient()),
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiMock.get).toHaveBeenCalledWith('/cycles/c-1')
    expect(result.current.data?.name).toBe('Sprint 1')
  })
})

describe('useCreateCycle', () => {
  it('posts the cycle payload and shows a success toast', async () => {
    apiMock.post.mockResolvedValue(mockCycle)
    const qc = makeQueryClient()
    const { result } = renderHook(() => useCreateCycle(), {
      wrapper: makeWrapper(qc),
    })

    await result.current.mutateAsync({
      team_id: 't-1',
      name: 'Sprint 1',
      starts_at: '2026-08-01',
      ends_at: '2026-08-14',
    })

    expect(apiMock.post).toHaveBeenCalledWith('/cycles', {
      team_id: 't-1',
      name: 'Sprint 1',
      starts_at: '2026-08-01',
      ends_at: '2026-08-14',
    })
    expect(toastMock.success).toHaveBeenCalledWith('Cycle created')
  })
})

describe('useUpdateCycle', () => {
  it('patches the cycle (excluding team_id from the body)', async () => {
    apiMock.patch.mockResolvedValue({ ...mockCycle, name: 'Renamed' })
    const { result } = renderHook(() => useUpdateCycle(), {
      wrapper: makeWrapper(makeQueryClient()),
    })

    await result.current.mutateAsync({
      id: 'c-1',
      team_id: 't-1',
      name: 'Renamed',
    })

    expect(apiMock.patch).toHaveBeenCalledWith('/cycles/c-1', { name: 'Renamed' })
    expect(toastMock.success).toHaveBeenCalledWith('Cycle updated')
  })
})

describe('useDeleteCycle', () => {
  it('deletes the cycle and shows a success toast', async () => {
    apiMock.delete.mockResolvedValue(undefined)
    const { result } = renderHook(() => useDeleteCycle(), {
      wrapper: makeWrapper(makeQueryClient()),
    })

    await result.current.mutateAsync({ id: 'c-1', team_id: 't-1' })

    expect(apiMock.delete).toHaveBeenCalledWith('/cycles/c-1')
    expect(toastMock.success).toHaveBeenCalledWith('Cycle deleted')
  })
})

describe('useCycleLookup', () => {
  it('resolves a cycle id to its name', async () => {
    authMock.isAuthenticated.mockReturnValue(true)
    apiMock.get.mockResolvedValue(mockCycles)
    const { result } = renderHook(() => useCycleLookup('t-1'), {
      wrapper: makeWrapper(makeQueryClient()),
    })
    await waitFor(() => expect(result.current('c-1')?.name).toBe('Sprint 1'))
    expect(result.current('unknown')).toBeUndefined()
    expect(result.current(null)).toBeUndefined()
  })
})
