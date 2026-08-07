import { describe, it, expect, vi, beforeEach } from 'vitest'
import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import {
  useIssueDependencies,
  useCreateIssueDependency,
  useDeleteIssueDependency,
  splitDependencies,
} from './useIssueDependencies'
import type { IssueDependency } from '@/types/issue-dependency'

const apiMock = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
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

function makeDep(id: string, blockerId: string, blockedId: string): IssueDependency {
  return {
    id,
    blocker_id: blockerId,
    blocked_id: blockedId,
    relation: 'blocks',
    blocker: {
      id: blockerId,
      identifier: 'ENG-1',
      title: 'Blocker',
      priority: 2,
      status_id: 's1',
    },
    blocked: {
      id: blockedId,
      identifier: 'ENG-2',
      title: 'Blocked',
      priority: 3,
      status_id: 's1',
    },
    created_at: '',
    updated_at: '',
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

describe('splitDependencies (reciprocal, VAL-DEPS-002)', () => {
  it('classifies "a blocks b" so a sees blocking and b sees blockedBy', () => {
    const dep = makeDep('d1', 'a', 'b')
    expect(splitDependencies([dep], 'a').blocking).toHaveLength(1)
    expect(splitDependencies([dep], 'a').blockedBy).toHaveLength(0)
    expect(splitDependencies([dep], 'b').blocking).toHaveLength(0)
    expect(splitDependencies([dep], 'b').blockedBy).toHaveLength(1)
  })

  it('returns empty lists for no dependencies', () => {
    expect(splitDependencies([], 'a')).toEqual({ blocking: [], blockedBy: [] })
  })
})

describe('useIssueDependencies', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    authMock.isAuthenticated.mockReturnValue(true)
  })

  it('lists dependencies for an issue', async () => {
    api.get.mockResolvedValue({
      items: [makeDep('d1', 'a', 'b')],
      total: 1,
      page: 1,
      size: 50,
      pages: 1,
    })
    const { result } = renderHook(() => useIssueDependencies('a', 'team-1'), {
      wrapper: W(),
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining('issue_id=a'),
    )
    expect(result.current.data?.items).toHaveLength(1)
  })

  it('is disabled without an issue id', async () => {
    const { result } = renderHook(() => useIssueDependencies(undefined, 'team-1'), {
      wrapper: W(),
    })
    expect(result.current.fetchStatus).toBe('idle')
    expect(api.get).not.toHaveBeenCalled()
  })
})

describe('useCreateIssueDependency', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    authMock.isAuthenticated.mockReturnValue(true)
  })

  it('POSTs the blocker/blocked pair', async () => {
    api.post.mockResolvedValue(makeDep('d1', 'a', 'b'))
    const { result } = renderHook(() => useCreateIssueDependency(), { wrapper: W() })
    result.current.mutate({
      blocker_id: 'a',
      blocked_id: 'b',
      team_id: 'team-1',
    })
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/issue-dependencies', {
        blocker_id: 'a',
        blocked_id: 'b',
      }),
    )
  })
})

describe('useDeleteIssueDependency', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    authMock.isAuthenticated.mockReturnValue(true)
  })

  it('DELETEs by dependency id', async () => {
    api.delete.mockResolvedValue(undefined)
    const { result } = renderHook(() => useDeleteIssueDependency(), { wrapper: W() })
    result.current.mutate({ id: 'd1', team_id: 'team-1' })
    await waitFor(() =>
      expect(api.delete).toHaveBeenCalledWith('/issue-dependencies/d1'),
    )
  })
})
