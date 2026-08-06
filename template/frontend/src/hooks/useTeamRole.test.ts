import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useTeamRole } from './useTeamRole'
import type { Team } from '@/types/team'

// useTeamRole derives the role from useTeams' enriched response (my_role).
const { useTeamsMock } = vi.hoisted(() => ({ useTeamsMock: vi.fn() }))
vi.mock('@/hooks/useTeams', () => ({ useTeams: useTeamsMock }))

function makeTeam(overrides: Partial<Team> = {}): Team {
  return {
    id: 't-1',
    name: 'Engineering',
    key: 'ENG',
    issue_sequence: 0,
    my_role: 'member',
    created_at: '',
    updated_at: '',
    deleted_at: null,
    ...overrides,
  }
}

function makeWrapper(qc: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: qc }, children)
  }
}

describe('useTeamRole', () => {
  beforeEach(() => {
    useTeamsMock.mockReset()
  })

  it('exposes an admin role and grants write + admin', () => {
    useTeamsMock.mockReturnValue({
      data: { items: [makeTeam({ key: 'ENG', my_role: 'admin' })] },
      isLoading: false,
    })
    const { result } = renderHook(() => useTeamRole('ENG'), {
      wrapper: makeWrapper(new QueryClient()),
    })
    expect(result.current.role).toBe('admin')
    expect(result.current.canWrite).toBe(true)
    expect(result.current.canAdmin).toBe(true)
  })

  it('exposes a member role: writes allowed, admin blocked', () => {
    useTeamsMock.mockReturnValue({
      data: { items: [makeTeam({ key: 'ENG', my_role: 'member' })] },
      isLoading: false,
    })
    const { result } = renderHook(() => useTeamRole('ENG'), {
      wrapper: makeWrapper(new QueryClient()),
    })
    expect(result.current.role).toBe('member')
    expect(result.current.canWrite).toBe(true)
    expect(result.current.canAdmin).toBe(false)
  })

  it('exposes a guest role: writes blocked, admin blocked (reads ok)', () => {
    useTeamsMock.mockReturnValue({
      data: { items: [makeTeam({ key: 'ENG', my_role: 'guest' })] },
      isLoading: false,
    })
    const { result } = renderHook(() => useTeamRole('ENG'), {
      wrapper: makeWrapper(new QueryClient()),
    })
    expect(result.current.role).toBe('guest')
    expect(result.current.canWrite).toBe(false)
    expect(result.current.canAdmin).toBe(false)
  })

  it('returns undefined role and no capabilities for a foreign team key', () => {
    useTeamsMock.mockReturnValue({
      data: { items: [makeTeam({ key: 'ENG', my_role: 'admin' })] },
      isLoading: false,
    })
    const { result } = renderHook(() => useTeamRole('OTHER'), {
      wrapper: makeWrapper(new QueryClient()),
    })
    expect(result.current.role).toBeUndefined()
    expect(result.current.canWrite).toBe(false)
    expect(result.current.canAdmin).toBe(false)
  })
})
