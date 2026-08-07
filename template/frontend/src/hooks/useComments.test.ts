import { describe, it, expect, vi, beforeEach } from 'vitest'
import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import {
  useComments,
  useCreateComment,
  useUpdateComment,
  useDeleteComment,
} from './useComments'
import { queryKeys } from '@/lib/query-keys'
import type { Comment } from '@/types/comment'

const apiMock = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
}))
const authMock = vi.hoisted(() => ({ isAuthenticated: vi.fn() }))
const toastMock = vi.hoisted(() => ({ success: vi.fn(), error: vi.fn() }))

vi.mock('@/lib/api-client', () => ({
  api: apiMock,
  ApiError: class ApiError extends Error {
    status: number
    code?: string
    fields?: Record<string, string[]>
    constructor(status: number, message: string, code?: string, fields?: Record<string, string[]>) {
      super(message)
      this.name = 'ApiError'
      this.status = status
      this.code = code
      this.fields = fields
    }
  },
}))
vi.mock('@/lib/auth', () => ({ isAuthenticated: authMock.isAuthenticated }))
vi.mock('sonner', () => ({ toast: toastMock }))

const api = apiMock

function makeComment(id: string, body: string, authorName = 'Ada'): Comment {
  return {
    id,
    issue_id: 'issue-1',
    author_id: 'u1',
    body,
    author: { id: 'u1', display_name: authorName, email: 'ada@x.com' },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  }
}

function makeWrapper(qc: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: qc }, children)
  }
}

/** Shared wrapper with retries disabled so tests fail fast. */
function W() {
  return makeWrapper(
    new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    }),
  )
}

describe('useComments', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    authMock.isAuthenticated.mockReturnValue(true)
  })

  it('lists comments for an issue (newest-first from backend)', async () => {
    api.get.mockResolvedValue({
      items: [makeComment('c2', 'second'), makeComment('c1', 'first')],
      total: 2,
      page: 1,
      size: 50,
      pages: 1,
    })
    const { result } = renderHook(() => useComments('issue-1', 'team-1'), {
      wrapper: W(),
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(api.get).toHaveBeenCalledWith(expect.stringContaining('issue_id=issue-1'))
    expect(result.current.data?.items).toHaveLength(2)
  })

  it('is disabled without an issue id', async () => {
    const { result } = renderHook(() => useComments(undefined, 'team-1'), {
      wrapper: W(),
    })
    expect(result.current.fetchStatus).toBe('idle')
    expect(api.get).not.toHaveBeenCalled()
  })
})

describe('useCreateComment', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    authMock.isAuthenticated.mockReturnValue(true)
  })

  it('optimistically prepends the comment before the POST resolves (VAL-COMMENTS-001)', async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    // Seed the thread cache with one existing comment.
    const key = queryKeys.comments.forIssue('issue-1')
    qc.setQueryData(key, {
      items: [makeComment('c1', 'first')],
      total: 1,
      page: 1,
      size: 50,
      pages: 1,
    })

    api.post.mockResolvedValue(
      makeComment('server-1', 'hello'),
    )
    const { result } = renderHook(() => useCreateComment(), {
      wrapper: makeWrapper(qc),
    })

    result.current.mutate({
      issue_id: 'issue-1',
      body: 'hello',
      author: { id: 'u1', display_name: 'Ada', email: 'ada@x.com' },
    })

    // Optimistic entry appears immediately at the top (before POST resolves).
    await waitFor(() => {
      const data = qc.getQueryData<{ items: Comment[] }>(key)
      expect(data?.items[0].body).toBe('hello')
      expect(data?.items[0].id).toMatch(/^optimistic-/)
    })
    expect(api.post).toHaveBeenCalledWith('/comments', {
      issue_id: 'issue-1',
      body: 'hello',
    })
  })

  it('rolls back the optimistic insert on error', async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const key = queryKeys.comments.forIssue('issue-1')
    const existing = {
      items: [makeComment('c1', 'first')],
      total: 1,
      page: 1,
      size: 50,
      pages: 1,
    }
    qc.setQueryData(key, existing)

    api.post.mockRejectedValue(new Error('boom'))
    const { result } = renderHook(() => useCreateComment(), {
      wrapper: makeWrapper(qc),
    })
    result.current.mutate({
      issue_id: 'issue-1',
      body: 'hello',
      author: { id: 'u1', display_name: 'Ada', email: 'ada@x.com' },
    })
    await waitFor(() => expect(result.current.isError).toBe(true))
    // The cache is restored to the pre-mutation snapshot (no optimistic entry).
    const data = qc.getQueryData<{ items: Comment[] }>(key)
    expect(data?.items).toHaveLength(1)
    expect(data?.items[0].id).toBe('c1')
  })
})

describe('useUpdateComment', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    authMock.isAuthenticated.mockReturnValue(true)
  })

  it('optimistically patches the body in place (VAL-COMMENTS-005)', async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const key = queryKeys.comments.forIssue('issue-1')
    qc.setQueryData(key, {
      items: [makeComment('c1', 'old')],
      total: 1,
      page: 1,
      size: 50,
      pages: 1,
    })

    api.patch.mockResolvedValue(makeComment('c1', 'edited'))
    const { result } = renderHook(() => useUpdateComment(), {
      wrapper: makeWrapper(qc),
    })
    result.current.mutate({ id: 'c1', body: 'edited' })

    await waitFor(() => {
      const data = qc.getQueryData<{ items: Comment[] }>(key)
      expect(data?.items[0].body).toBe('edited')
    })
    expect(api.patch).toHaveBeenCalledWith('/comments/c1', { body: 'edited' })
    // No duplicate comment added (edit in place, not a new entry).
    expect(qc.getQueryData<{ items: Comment[] }>(key)?.items).toHaveLength(1)
  })
})

describe('useDeleteComment', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    authMock.isAuthenticated.mockReturnValue(true)
  })

  it('optimistically removes the comment (VAL-COMMENTS-006)', async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const key = queryKeys.comments.forIssue('issue-1')
    qc.setQueryData(key, {
      items: [makeComment('c1', 'a'), makeComment('c2', 'b')],
      total: 2,
      page: 1,
      size: 50,
      pages: 1,
    })

    api.delete.mockResolvedValue(undefined)
    const { result } = renderHook(() => useDeleteComment(), {
      wrapper: makeWrapper(qc),
    })
    result.current.mutate({ id: 'c1' })

    await waitFor(() => {
      const data = qc.getQueryData<{ items: Comment[] }>(key)
      expect(data?.items).toHaveLength(1)
    })
    expect(api.delete).toHaveBeenCalledWith('/comments/c1')
  })
})
