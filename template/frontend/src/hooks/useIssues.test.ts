import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import {
  useIssues,
  useCreateIssue,
  isOptimisticIssue,
  flattenIssues,
  issuesTotal,
} from './useIssues'
import type { IssuesResponse, Issue, CreateIssueInput } from '@/types/issue'

const apiMock = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
}))
const authMock = vi.hoisted(() => ({ isAuthenticated: vi.fn() }))
const toastMock = vi.hoisted(() => ({
  success: vi.fn(),
  error: vi.fn(),
}))
// Provide a real ApiError class so toastApiError's `instanceof` check works.
const { ApiError } = vi.hoisted(() => ({
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      message: string,
    ) {
      super(message)
      this.name = 'ApiError'
    }
  },
}))

vi.mock('@/lib/api-client', () => ({ api: apiMock, ApiError }))
vi.mock('@/lib/auth', () => ({
  isAuthenticated: authMock.isAuthenticated,
}))
vi.mock('sonner', () => ({
  toast: toastMock,
}))

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}
function makeWrapper(qc: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: qc }, children)
  }
}

const realIssue: Issue = {
  id: 'i-1',
  team_id: 't-1',
  identifier: 'ENG-1',
  title: 'Existing',
  description: null,
  status_id: 'ws-1',
  priority: 4,
  assignee_id: null,
  creator_id: 'u-1',
  project_id: null,
  cycle_id: null,
  parent_id: null,
  sort_order: 0,
  estimate: null,
  due_date: null,
  labels: [],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

/** A single default page (size 50, page 1 of 1). */
const mockPage: IssuesResponse = {
  items: [realIssue],
  total: 1,
  page: 1,
  size: 50,
  pages: 1,
}

const createInput: CreateIssueInput = {
  team_id: 't-1',
  title: 'New issue',
  description: 'body',
  status_id: 'ws-1',
  priority: 4,
}

describe('useIssues (infinite query)', () => {
  beforeEach(() => {
    apiMock.get.mockReset()
    authMock.isAuthenticated.mockReset()
  })

  it('fetches the first page scoped to the team with size/page/order_by', async () => {
    authMock.isAuthenticated.mockReturnValue(true)
    apiMock.get.mockResolvedValue(mockPage)

    const { result } = renderHook(() => useIssues('t-1'), {
      wrapper: makeWrapper(makeQueryClient()),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiMock.get).toHaveBeenCalledWith(
      '/issues?team_id=t-1&size=50&page=1&order_by=-created_at',
    )
  })

  it('is disabled without a teamId', () => {
    authMock.isAuthenticated.mockReturnValue(true)
    const { result } = renderHook(() => useIssues(undefined), {
      wrapper: makeWrapper(makeQueryClient()),
    })
    expect(result.current.fetchStatus).toBe('idle')
    expect(apiMock.get).not.toHaveBeenCalled()
  })

  it('polls the list (refetchInterval set on the query options)', async () => {
    authMock.isAuthenticated.mockReturnValue(true)
    apiMock.get.mockResolvedValue(mockPage)
    const qc = makeQueryClient()

    renderHook(() => useIssues('t-1'), { wrapper: makeWrapper(qc) })
    await waitFor(() => expect(apiMock.get).toHaveBeenCalled())

    const query = qc.getQueryCache().find({ queryKey: ['issues', 'list', 't-1', ''] })
    expect((query?.options as { refetchInterval?: number }).refetchInterval).toBe(8000)
  })

  it('encodes filter/search/sort params into the query string', async () => {
    authMock.isAuthenticated.mockReturnValue(true)
    apiMock.get.mockResolvedValue(mockPage)

    const { result } = renderHook(
      () =>
        useIssues('t-1', {
          search: 'bug report',
          status_id: 'ws-2',
          priority: 0,
          assignee: 'unassigned',
          label_id: 'lab-1',
          sort: 'priority',
        }),
      { wrapper: makeWrapper(makeQueryClient()) },
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    const calledUrl = apiMock.get.mock.calls[0][0] as string
    // search is URL-encoded; assert the decoded params are present.
    expect(calledUrl).toContain('team_id=t-1')
    expect(calledUrl).toContain('size=50')
    expect(calledUrl).toContain('page=1')
    expect(calledUrl).toContain('search=bug+report')
    expect(calledUrl).toContain('status_id=ws-2')
    expect(calledUrl).toContain('priority=0')
    expect(calledUrl).toContain('unassigned=true')
    expect(calledUrl).toContain('label_id=lab-1')
    // priority sort → two order_by fields (priority then -created_at tiebreaker).
    expect(calledUrl).toContain('order_by=priority')
    expect(calledUrl).toContain('order_by=-created_at')
  })

  it('exposes hasNextPage when more pages remain', async () => {
    authMock.isAuthenticated.mockReturnValue(true)
    apiMock.get.mockResolvedValue({ ...mockPage, total: 75, pages: 2 })

    const { result } = renderHook(() => useIssues('t-1'), {
      wrapper: makeWrapper(makeQueryClient()),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.hasNextPage).toBe(true)
  })

  it('flattenIssues / issuesTotal derive from the infinite cache', () => {
    const data = {
      pages: [mockPage, { ...mockPage, items: [realIssue], page: 2 }],
      pageParams: [1, 2],
    } as never
    expect(flattenIssues(data)).toHaveLength(2)
    expect(issuesTotal(data)).toBe(1)
    expect(flattenIssues(undefined)).toEqual([])
    expect(issuesTotal(undefined)).toBe(0)
  })
})

describe('useCreateIssue — optimistic insert + rollback', () => {
  beforeEach(() => {
    apiMock.get.mockReset()
    apiMock.post.mockReset()
    toastMock.success.mockReset()
    toastMock.error.mockReset()
    authMock.isAuthenticated.mockReturnValue(true)
    apiMock.get.mockResolvedValue(mockPage)
  })

  it('prepends an optimistic row to the default view before the POST resolves', async () => {
    const qc = makeQueryClient()

    // Mount useIssues so the list query has an active observer — that way the
    // invalidation in onSettled actually triggers a refetch to reconcile.
    const { result } = renderHook(
      () => ({ list: useIssues('t-1'), create: useCreateIssue() }),
      { wrapper: makeWrapper(qc) },
    )
    await waitFor(() => expect(result.current.list.isSuccess).toBe(true))

    // Hold the POST open so we can inspect the in-flight optimistic cache.
    let resolvePost!: (v: Issue) => void
    apiMock.post.mockReturnValue(
      new Promise<Issue>((res) => {
        resolvePost = res
      }),
    )

    const createdIssue: Issue = {
      ...realIssue,
      id: 'i-2',
      identifier: 'ENG-2',
      title: 'New issue',
    }

    act(() => {
      result.current.create.mutate(createInput)
    })

    // While the POST is in flight, the optimistic row is already in the first
    // page (VAL-ISSUES-008) and the count reflects it.
    await waitFor(() => {
      const data = qc.getQueryData<{
        pages: IssuesResponse[]
        pageParams: number[]
      }>(['issues', 'list', 't-1', ''])
      const first = data?.pages[0]
      expect(first?.items.some((i) => i.id.startsWith('optimistic-'))).toBe(true)
      expect(first?.total).toBe(2)
    })

    // Resolve the POST → onSettled invalidates → observed refetch reconciles.
    apiMock.get.mockResolvedValue({
      items: [createdIssue, realIssue],
      total: 2,
      page: 1,
      size: 50,
      pages: 1,
    })
    resolvePost(createdIssue)

    await waitFor(() => expect(result.current.create.isSuccess).toBe(true))
    await waitFor(() => {
      const data = qc.getQueryData<{
        pages: IssuesResponse[]
        pageParams: number[]
      }>(['issues', 'list', 't-1', ''])
      expect(data?.pages[0].items.some((i) => i.identifier === 'ENG-2')).toBe(true)
    })
    expect(toastMock.success).toHaveBeenCalled()
  })

  it('does NOT prepend to a filtered view (only the default view)', async () => {
    const qc = makeQueryClient()
    // Seed a filtered-view cache entry directly.
    const filteredKey = ['issues', 'list', 't-1', 'q:bug']
    qc.setQueryData(filteredKey, {
      pages: [mockPage],
      pageParams: [1],
    })

    apiMock.post.mockResolvedValue({ ...realIssue, id: 'i-9', identifier: 'ENG-9' })

    const { result } = renderHook(() => useCreateIssue(), { wrapper: makeWrapper(qc) })
    await act(async () => {
      await result.current.mutateAsync(createInput)
    })

    const data = qc.getQueryData<{
      pages: IssuesResponse[]
      pageParams: number[]
    }>(filteredKey)
    // No optimistic row leaked into the filtered view.
    expect(data?.pages[0].items.some((i) => i.id.startsWith('optimistic-'))).toBe(false)
    expect(data?.pages[0].total).toBe(1)
  })

  it('rolls back the optimistic row on backend error', async () => {
    const qc = makeQueryClient()
    qc.setQueryData(['issues', 'list', 't-1', ''], {
      pages: [mockPage],
      pageParams: [1],
    })

    apiMock.post.mockRejectedValue(new ApiError(422, 'Invalid'))

    const { result } = renderHook(() => useCreateIssue(), { wrapper: makeWrapper(qc) })

    await act(async () => {
      try {
        await result.current.mutateAsync(createInput)
      } catch {
        // expected to reject
      }
    })

    // Cache rolled back to the original snapshot (no optimistic row left).
    await waitFor(() => {
      const data = qc.getQueryData<{
        pages: IssuesResponse[]
        pageParams: number[]
      }>(['issues', 'list', 't-1', ''])
      expect(data?.pages[0].items).toHaveLength(1)
      expect(data?.pages[0].items[0].id).toBe('i-1')
    })
    expect(toastMock.error).toHaveBeenCalled()
  })

  it('does not send the optimistic-only labels field to the API', async () => {
    const qc = makeQueryClient()
    qc.setQueryData(['issues', 'list', 't-1', ''], {
      pages: [mockPage],
      pageParams: [1],
    })
    apiMock.post.mockResolvedValue({ ...realIssue, id: 'i-3' })

    const { result } = renderHook(() => useCreateIssue(), { wrapper: makeWrapper(qc) })

    await act(async () => {
      await result.current.mutateAsync({
        ...createInput,
        optimisticLabels: [{ id: 'l-1', team_id: 't-1', name: 'Bug', color: '#f00' }],
      })
    })

    expect(apiMock.post).toHaveBeenCalledWith(
      '/issues',
      expect.not.objectContaining({ optimisticLabels: expect.anything() }),
    )
  })
})

describe('isOptimisticIssue', () => {
  it('flags optimistic ids and rejects real ids', () => {
    expect(isOptimisticIssue({ ...realIssue, id: 'optimistic-abc' })).toBe(true)
    expect(isOptimisticIssue(realIssue)).toBe(false)
  })
})
