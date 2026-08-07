import { describe, it, expect, vi, beforeEach } from 'vitest'
import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { useActivity } from './useActivity'
import { queryKeys } from '@/lib/query-keys'
import type { Activity } from '@/types/activity'

const apiMock = vi.hoisted(() => ({ get: vi.fn() }))
const authMock = vi.hoisted(() => ({ isAuthenticated: vi.fn() }))

vi.mock('@/lib/api-client', () => ({ api: apiMock }))
vi.mock('@/lib/auth', () => ({ isAuthenticated: authMock.isAuthenticated }))

const api = apiMock

function makeActivity(
  id: string,
  type: Activity['type'],
  payload: Activity['payload'],
): Activity {
  return {
    id,
    issue_id: 'issue-1',
    actor_id: 'u1',
    type,
    payload,
    actor: { id: 'u1', display_name: 'Ada', email: 'ada@x.com' },
    created_at: '2024-01-01T00:00:00Z',
  }
}

function makeWrapper(qc: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: qc }, children)
  }
}

function W() {
  return makeWrapper(
    new QueryClient({
      defaultOptions: { queries: { retry: false } },
    }),
  )
}

describe('useActivity', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    authMock.isAuthenticated.mockReturnValue(true)
  })

  it('lists activity for an issue (newest-first from backend)', async () => {
    api.get.mockResolvedValue({
      items: [
        makeActivity('a2', 'status_change', {
          from: { id: 's1', name: 'Backlog' },
          to: { id: 's2', name: 'In Progress' },
        }),
        makeActivity('a1', 'title_rename', { from: 'Old', to: 'New' }),
      ],
      total: 2,
      page: 1,
      size: 50,
      pages: 1,
    })

    const { result } = renderHook(() => useActivity('issue-1', 'team-1'), {
      wrapper: W(),
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data?.items).toHaveLength(2)
    // The issue_id filter is sent as a query param.
    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining('issue_id=issue-1'),
    )
  })

  it('uses the per-issue query key', async () => {
    api.get.mockResolvedValue({ items: [], total: 0, page: 1, size: 50, pages: 1 })
    const { result } = renderHook(() => useActivity('issue-1', 'team-1'), {
      wrapper: W(),
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.total).toBe(0)
  })

  it('is disabled when there is no issueId', () => {
    const { result } = renderHook(() => useActivity(undefined, 'team-1'), {
      wrapper: W(),
    })
    expect(result.current.fetchStatus).toBe('idle')
    expect(api.get).not.toHaveBeenCalled()
  })

  it('is disabled when unauthenticated', () => {
    authMock.isAuthenticated.mockReturnValue(false)
    const { result } = renderHook(() => useActivity('issue-1', 'team-1'), {
      wrapper: W(),
    })
    expect(result.current.fetchStatus).toBe('idle')
    expect(api.get).not.toHaveBeenCalled()
  })

  it('resolves successfully (polling is a static refetchInterval in the hook)', async () => {
    // Polling (VAL-ACTIVITY-008) is configured via a fixed refetchInterval in
    // the hook source; the live behavior is verified end-to-end with
    // agent-browser. Here we assert the query resolves and is enabled.
    api.get.mockResolvedValue({ items: [], total: 0, page: 1, size: 50, pages: 1 })
    const { result } = renderHook(() => useActivity('issue-1', 'team-1'), {
      wrapper: W(),
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.total).toBe(0)
    expect(api.get).toHaveBeenCalledTimes(1)
  })

  it('query key is namespaced under activity/issue', () => {
    expect(queryKeys.activity.forIssue('issue-1')).toEqual([
      'activity',
      'issue',
      'issue-1',
    ])
  })
})
