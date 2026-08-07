import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useTeamAccessGuard } from './useTeamAccessGuard'
import type { Team } from '@/types/team'

const { useTeamsMock } = vi.hoisted(() => ({ useTeamsMock: vi.fn() }))
const { navigateMock } = vi.hoisted(() => ({ navigateMock: vi.fn() }))
const { isAuthenticatedMock } = vi.hoisted(() => ({ isAuthenticatedMock: vi.fn() }))

vi.mock('@/hooks/useTeams', () => ({
  useTeams: useTeamsMock,
  pickDefaultTeam: (teams: Team[] | undefined) =>
    teams && teams.length > 0 ? teams[0] : null,
}))
vi.mock('@tanstack/react-router', () => ({ useNavigate: () => navigateMock }))
vi.mock('@/lib/auth', () => ({ isAuthenticated: isAuthenticatedMock }))

function makeTeam(key: string): Team {
  return {
    id: `t-${key}`,
    name: key,
    key,
    issue_sequence: 0,
    my_role: 'admin',
    created_at: '',
    updated_at: '',
    deleted_at: null,
  }
}

function makeWrapper(qc: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: qc }, children)
  }
}

describe('useTeamAccessGuard', () => {
  beforeEach(() => {
    useTeamsMock.mockReset()
    navigateMock.mockReset()
    isAuthenticatedMock.mockReset()
    // Authenticated by default (the team guard is meaningful for signed-in users).
    isAuthenticatedMock.mockReturnValue(true)
  })

  it('does not redirect when the team key belongs to the user (valid)', () => {
    useTeamsMock.mockReturnValue({
      data: { items: [makeTeam('ENG')] },
      isLoading: false,
    })
    const { result } = renderHook(() => useTeamAccessGuard('ENG'), {
      wrapper: makeWrapper(new QueryClient()),
    })
    expect(result.current.isValid).toBe(true)
    expect(navigateMock).not.toHaveBeenCalled()
  })

  it('redirects to the default team when the key is foreign (cross-team)', async () => {
    useTeamsMock.mockReturnValue({
      data: { items: [makeTeam('ENG')] },
      isLoading: false,
    })
    renderHook(() => useTeamAccessGuard('FOREIGN'), {
      wrapper: makeWrapper(new QueryClient()),
    })
    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith({
        to: '/$team/issues',
        params: { team: 'ENG' },
        replace: true,
      })
    })
  })

  it('does not redirect while teams are still loading', () => {
    useTeamsMock.mockReturnValue({ data: undefined, isLoading: true })
    renderHook(() => useTeamAccessGuard('FOREIGN'), {
      wrapper: makeWrapper(new QueryClient()),
    })
    expect(navigateMock).not.toHaveBeenCalled()
  })

  it('does not redirect when there is no team key (e.g. /workspace)', () => {
    useTeamsMock.mockReturnValue({
      data: { items: [makeTeam('ENG')] },
      isLoading: false,
    })
    renderHook(() => useTeamAccessGuard(undefined), {
      wrapper: makeWrapper(new QueryClient()),
    })
    expect(navigateMock).not.toHaveBeenCalled()
  })

  it('does not redirect for an unauthenticated user (auth guard handles it)', () => {
    // An unauth user has no teams (401); the team guard must NOT bounce the URL
    // so the _authed layout captures the original deep-link path for /login.
    isAuthenticatedMock.mockReturnValue(false)
    useTeamsMock.mockReturnValue({ data: { items: [] }, isLoading: false })
    renderHook(() => useTeamAccessGuard('FOREIGN'), {
      wrapper: makeWrapper(new QueryClient()),
    })
    expect(navigateMock).not.toHaveBeenCalled()
  })
})
