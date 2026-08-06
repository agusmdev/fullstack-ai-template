import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useIssues, useCreateIssue, isOptimisticIssue } from './useIssues'
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

const mockResponse: IssuesResponse = {
  items: [realIssue],
  total: 1,
  page: 1,
  size: 200,
  pages: 1,
}

const createInput: CreateIssueInput = {
  team_id: 't-1',
  title: 'New issue',
  description: 'body',
  status_id: 'ws-1',
  priority: 4,
}

describe('useIssues', () => {
  beforeEach(() => {
    apiMock.get.mockReset()
    authMock.isAuthenticated.mockReset()
  })

  it('fetches issues scoped to the team when authenticated', async () => {
    authMock.isAuthenticated.mockReturnValue(true)
    apiMock.get.mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useIssues('t-1'), {
      wrapper: makeWrapper(makeQueryClient()),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiMock.get).toHaveBeenCalledWith('/issues?team_id=t-1&size=100')
    expect(result.current.data?.items).toHaveLength(1)
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
    apiMock.get.mockResolvedValue(mockResponse)
    const qc = makeQueryClient()

    renderHook(() => useIssues('t-1'), { wrapper: makeWrapper(qc) })
    await waitFor(() => expect(apiMock.get).toHaveBeenCalled())

    const query = qc.getQueryCache().find({ queryKey: ['issues', 'list', 't-1'] })
    expect((query?.options as { refetchInterval?: number }).refetchInterval).toBe(8000)
  })
})

describe('useCreateIssue — optimistic insert + rollback', () => {
  beforeEach(() => {
    apiMock.get.mockReset()
    apiMock.post.mockReset()
    toastMock.success.mockReset()
    toastMock.error.mockReset()
    authMock.isAuthenticated.mockReturnValue(true)
    // Default refetch (after invalidation) returns the original list.
    apiMock.get.mockResolvedValue(mockResponse)
  })

  it('prepends an optimistic row before the POST resolves', async () => {
    const qc = makeQueryClient()
    apiMock.get.mockResolvedValue(mockResponse)

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

    // While the POST is in flight, the optimistic row is already in the cache
    // (VAL-ISSUES-008) and the count reflects it.
    await waitFor(() => {
      const data = qc.getQueryData<IssuesResponse>(['issues', 'list', 't-1'])
      expect(data?.items.some((i) => i.id.startsWith('optimistic-'))).toBe(true)
      expect(data?.total).toBe(2)
    })

    // Resolve the POST → onSettled invalidates → observed refetch reconciles.
    apiMock.get.mockResolvedValue({
      items: [createdIssue, realIssue],
      total: 2,
      page: 1,
      size: 200,
      pages: 1,
    })
    resolvePost(createdIssue)

    await waitFor(() => expect(result.current.create.isSuccess).toBe(true))
    await waitFor(() => {
      const data = qc.getQueryData<IssuesResponse>(['issues', 'list', 't-1'])
      expect(data?.items.some((i) => i.identifier === 'ENG-2')).toBe(true)
    })
    expect(toastMock.success).toHaveBeenCalled()
  })

  it('rolls back the optimistic row on backend error', async () => {
    const qc = makeQueryClient()
    qc.setQueryData(['issues', 'list', 't-1'], mockResponse)

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
      const data = qc.getQueryData<IssuesResponse>(['issues', 'list', 't-1'])
      expect(data?.items).toHaveLength(1)
      expect(data?.items[0].id).toBe('i-1')
    })
    expect(toastMock.error).toHaveBeenCalled()
  })

  it('does not send the optimistic-only labels field to the API', async () => {
    const qc = makeQueryClient()
    qc.setQueryData(['issues', 'list', 't-1'], mockResponse)
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
