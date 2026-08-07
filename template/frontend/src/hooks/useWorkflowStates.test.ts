import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useWorkflowStates } from './useWorkflowStates'
import type { WorkflowStatesResponse } from '@/types/workflow-state'

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

const mockStates: WorkflowStatesResponse = {
  items: [
    { id: 'ws-1', team_id: 't-1', name: 'Backlog', type: 'backlog', position: 0, color: '#aaa' },
    { id: 'ws-2', team_id: 't-1', name: 'Todo', type: 'unstarted', position: 1, color: '#bbb' },
  ],
  total: 2,
  page: 1,
  size: 100,
  pages: 1,
}

describe('useWorkflowStates', () => {
  beforeEach(() => {
    apiMock.get.mockReset()
    authMock.isAuthenticated.mockReset()
  })

  it('fetches workflow states scoped to the team when authenticated', async () => {
    authMock.isAuthenticated.mockReturnValue(true)
    apiMock.get.mockResolvedValue(mockStates)

    const { result } = renderHook(() => useWorkflowStates('t-1'), {
      wrapper: makeWrapper(makeQueryClient()),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiMock.get).toHaveBeenCalledWith('/workflow-states?team_id=t-1&size=100')
    expect(result.current.data?.items).toHaveLength(2)
  })

  it('is disabled without a teamId', () => {
    authMock.isAuthenticated.mockReturnValue(true)
    const { result } = renderHook(() => useWorkflowStates(undefined), {
      wrapper: makeWrapper(makeQueryClient()),
    })
    expect(result.current.fetchStatus).toBe('idle')
    expect(apiMock.get).not.toHaveBeenCalled()
  })
})
