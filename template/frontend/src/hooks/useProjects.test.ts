import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import {
  useProjects,
  useProject,
  useCreateProject,
  useUpdateProject,
  useDeleteProject,
  useProjectLookup,
} from './useProjects'
import type { ProjectsResponse, Project } from '@/types/project'

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

const mockProject: Project = {
  id: 'p-1',
  team_id: 't-1',
  name: 'Q3 Launch',
  status: 'planned',
  lead_id: null,
  target_date: null,
  description: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

const mockProjects: ProjectsResponse = {
  items: [mockProject],
  total: 1,
  page: 1,
  size: 100,
  pages: 1,
}

describe('useProjects', () => {
  beforeEach(() => {
    apiMock.get.mockReset()
    apiMock.post.mockReset()
    apiMock.patch.mockReset()
    apiMock.delete.mockReset()
    authMock.isAuthenticated.mockReset()
    toastMock.success.mockReset()
  })

  it('fetches projects scoped to the team when authenticated', async () => {
    authMock.isAuthenticated.mockReturnValue(true)
    apiMock.get.mockResolvedValue(mockProjects)

    const { result } = renderHook(() => useProjects('t-1'), {
      wrapper: makeWrapper(makeQueryClient()),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiMock.get).toHaveBeenCalledWith(
      expect.stringContaining('/projects?team_id=t-1'),
    )
    expect(result.current.data?.items).toHaveLength(1)
  })

  it('is disabled without a teamId', () => {
    authMock.isAuthenticated.mockReturnValue(true)
    const { result } = renderHook(() => useProjects(undefined), {
      wrapper: makeWrapper(makeQueryClient()),
    })
    expect(result.current.fetchStatus).toBe('idle')
    expect(apiMock.get).not.toHaveBeenCalled()
  })
})

describe('useProject', () => {
  beforeEach(() => {
    authMock.isAuthenticated.mockReturnValue(true)
    apiMock.get.mockReset()
  })

  it('fetches a single project by id', async () => {
    apiMock.get.mockResolvedValue(mockProject)
    const { result } = renderHook(() => useProject('p-1'), {
      wrapper: makeWrapper(makeQueryClient()),
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiMock.get).toHaveBeenCalledWith('/projects/p-1')
    expect(result.current.data?.name).toBe('Q3 Launch')
  })
})

describe('useCreateProject', () => {
  it('posts the project payload and shows a success toast', async () => {
    apiMock.post.mockResolvedValue(mockProject)
    const qc = makeQueryClient()
    const { result } = renderHook(() => useCreateProject(), {
      wrapper: makeWrapper(qc),
    })

    await result.current.mutateAsync({
      team_id: 't-1',
      name: 'Q3 Launch',
      status: 'planned',
    })

    expect(apiMock.post).toHaveBeenCalledWith('/projects', {
      team_id: 't-1',
      name: 'Q3 Launch',
      status: 'planned',
    })
    expect(toastMock.success).toHaveBeenCalledWith('Project created')
  })
})

describe('useUpdateProject', () => {
  it('patches the project (excluding team_id from the body)', async () => {
    apiMock.patch.mockResolvedValue({ ...mockProject, name: 'Renamed' })
    const { result } = renderHook(() => useUpdateProject(), {
      wrapper: makeWrapper(makeQueryClient()),
    })

    await result.current.mutateAsync({
      id: 'p-1',
      team_id: 't-1',
      name: 'Renamed',
    })

    expect(apiMock.patch).toHaveBeenCalledWith('/projects/p-1', { name: 'Renamed' })
    expect(toastMock.success).toHaveBeenCalledWith('Project updated')
  })
})

describe('useDeleteProject', () => {
  it('deletes the project and shows a success toast', async () => {
    apiMock.delete.mockResolvedValue(undefined)
    const { result } = renderHook(() => useDeleteProject(), {
      wrapper: makeWrapper(makeQueryClient()),
    })

    await result.current.mutateAsync({ id: 'p-1', team_id: 't-1' })

    expect(apiMock.delete).toHaveBeenCalledWith('/projects/p-1')
    expect(toastMock.success).toHaveBeenCalledWith('Project deleted')
  })
})

describe('useProjectLookup', () => {
  it('resolves a project id to its name', async () => {
    authMock.isAuthenticated.mockReturnValue(true)
    apiMock.get.mockResolvedValue(mockProjects)
    const { result } = renderHook(() => useProjectLookup('t-1'), {
      wrapper: makeWrapper(makeQueryClient()),
    })
    await waitFor(() => expect(result.current('p-1')?.name).toBe('Q3 Launch'))
    expect(result.current('unknown')).toBeUndefined()
    expect(result.current(null)).toBeUndefined()
  })
})
