import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Sidebar } from './Sidebar'
import type { Team } from '@/types/team'

const { useTeamsMock } = vi.hoisted(() => ({ useTeamsMock: vi.fn() }))
const { navigateMock } = vi.hoisted(() => ({ navigateMock: vi.fn() }))
const { useViewsMock } = vi.hoisted(() => ({ useViewsMock: vi.fn() }))

vi.mock('@/hooks/useTeams', () => ({ useTeams: useTeamsMock }))
vi.mock('@/hooks/useViews', () => ({
  useViews: useViewsMock,
  useDeleteView: () => ({ mutate: vi.fn() }),
}))
vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => navigateMock,
  useRouterState: ({ select }: { select?: (s: unknown) => unknown }) =>
    select
      ? select({ location: { search: {}, pathname: '/ENG/issues' } })
      : { location: { search: {}, pathname: '/ENG/issues' } },
  Link: ({
    to,
    params,
    children,
  }: {
    to: string
    params: Record<string, string>
    children: React.ReactNode
  }) => React.createElement('a', { href: to, 'data-team': params.team }, children),
}))

function makeTeam(key: string, name: string, role: Team['my_role'] = 'admin'): Team {
  return {
    id: `t-${key}`,
    name,
    key,
    issue_sequence: 0,
    my_role: role,
    created_at: '',
    updated_at: '',
    deleted_at: null,
  }
}

function renderSidebar(teamKey?: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <Sidebar teamKey={teamKey} />
    </QueryClientProvider>,
  )
}

describe('Sidebar team switcher', () => {
  beforeEach(() => {
    useTeamsMock.mockReset()
    navigateMock.mockReset()
    // Saved-views section defaults to empty (no saved views).
    useViewsMock.mockReturnValue({ data: { items: [] }, isLoading: false })
  })

  it('renders the active team identity', () => {
    useTeamsMock.mockReturnValue({
      data: { items: [makeTeam('ENG', 'Engineering')] },
      isLoading: false,
    })
    renderSidebar('ENG')
    expect(screen.getByText('Engineering')).toBeInTheDocument()
    expect(screen.getByText('ENG')).toBeInTheDocument()
  })

  it('lists every team when opened', () => {
    useTeamsMock.mockReturnValue({
      data: {
        items: [makeTeam('ENG', 'Engineering'), makeTeam('DESIGN', 'Design')],
      },
      isLoading: false,
    })
    renderSidebar('ENG')

    // Before opening, only the active team identity is visible.
    expect(screen.queryByText('Design')).not.toBeInTheDocument()

    fireEvent.click(screen.getByLabelText('Switch team'))
    // After opening, both teams are listed (Design only appears in the menu).
    expect(screen.getByText('Design')).toBeInTheDocument()
    expect(screen.getAllByText('Engineering').length).toBeGreaterThanOrEqual(1)
  })

  it('navigates to the selected team issues view on switch (re-scopes)', () => {
    useTeamsMock.mockReturnValue({
      data: {
        items: [makeTeam('ENG', 'Engineering'), makeTeam('DESIGN', 'Design')],
      },
      isLoading: false,
    })
    renderSidebar('ENG')

    fireEvent.click(screen.getByLabelText('Switch team'))
    fireEvent.click(screen.getByText('Design'))

    expect(navigateMock).toHaveBeenCalledWith({
      to: '/$team/issues',
      params: { team: 'DESIGN' },
    })
  })
})
