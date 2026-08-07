import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import {
  useViews,
  useCreateView,
  useUpdateView,
  useDeleteView,
} from './useViews'
import type { ViewsResponse, View } from '@/types/view'

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

vi.mock('@/lib/api-client', () => ({
  api: apiMock,
}))
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

const mockView: View = {
  id: 'v-1',
  owner_id: 'u-1',
  team_id: 't-1',
  name: 'Urgent bugs',
  filters: { status_id: 'st-1', priority: 0 },
  group_by: 'status',
  order_by: 'priority',
  description: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

const mockViews: ViewsResponse = {
  items: [mockView],
  total: 1,
  page: 1,
  size: 100,
  pages: 1,
}

describe('useViews', () => {
  beforeEach(() => {
    apiMock.get.mockReset()
    authMock.isAuthenticated.mockReset()
    toastMock.success.mockReset()
  })

  it('fetches views scoped to the team when authenticated', async () => {
    authMock.isAuthenticated.mockReturnValue(true)
    apiMock.get.mockResolvedValue(mockViews)

    const { result } = renderHook(() => useViews('t-1'), {
      wrapper: makeWrapper(makeQueryClient()),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiMock.get).toHaveBeenCalledWith(
      expect.stringContaining('/views?team_id=t-1'),
    )
    expect(result.current.data?.items).toHaveLength(1)
  })

  it('is disabled without a teamId', () => {
    authMock.isAuthenticated.mockReturnValue(true)
    const { result } = renderHook(() => useViews(undefined), {
      wrapper: makeWrapper(makeQueryClient()),
    })
    expect(result.current.fetchStatus).toBe('idle')
    expect(apiMock.get).not.toHaveBeenCalled()
  })
})

describe('useCreateView', () => {
  beforeEach(() => {
    apiMock.post.mockReset()
    toastMock.success.mockReset()
  })

  it('posts the view payload (filters + group_by + order_by) and toasts success', async () => {
    apiMock.post.mockResolvedValue(mockView)
    const { result } = renderHook(() => useCreateView(), {
      wrapper: makeWrapper(makeQueryClient()),
    })

    await result.current.mutateAsync({
      team_id: 't-1',
      name: 'Urgent bugs',
      filters: { status_id: 'st-1', priority: 0 },
      group_by: 'status',
      order_by: 'priority',
    })

    expect(apiMock.post).toHaveBeenCalledWith('/views', {
      team_id: 't-1',
      name: 'Urgent bugs',
      filters: { status_id: 'st-1', priority: 0 },
      group_by: 'status',
      order_by: 'priority',
    })
    expect(toastMock.success).toHaveBeenCalledWith('View saved')
  })
})

describe('useUpdateView', () => {
  beforeEach(() => {
    apiMock.patch.mockReset()
    toastMock.success.mockReset()
  })

  it('patches the view (excluding id + team_id from the body)', async () => {
    apiMock.patch.mockResolvedValue({ ...mockView, name: 'Renamed' })
    const { result } = renderHook(() => useUpdateView(), {
      wrapper: makeWrapper(makeQueryClient()),
    })

    await result.current.mutateAsync({
      id: 'v-1',
      team_id: 't-1',
      name: 'Renamed',
    })

    expect(apiMock.patch).toHaveBeenCalledWith('/views/v-1', { name: 'Renamed' })
    expect(toastMock.success).toHaveBeenCalledWith('View updated')
  })
})

describe('useDeleteView', () => {
  beforeEach(() => {
    apiMock.delete.mockReset()
    toastMock.success.mockReset()
  })

  it('deletes the view and shows a success toast', async () => {
    apiMock.delete.mockResolvedValue(undefined)
    const { result } = renderHook(() => useDeleteView(), {
      wrapper: makeWrapper(makeQueryClient()),
    })

    await result.current.mutateAsync({ id: 'v-1', team_id: 't-1' })

    expect(apiMock.delete).toHaveBeenCalledWith('/views/v-1')
    expect(toastMock.success).toHaveBeenCalledWith('View deleted')
  })
})
