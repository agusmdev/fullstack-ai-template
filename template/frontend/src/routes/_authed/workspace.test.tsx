import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Route } from './workspace'
import type { TeamsResponse } from '@/types/team'

// Mock useTeams + pickDefaultTeam so we control the data the workspace sees.
const { useTeamsMock } = vi.hoisted(() => ({
  useTeamsMock: vi.fn(),
}))
vi.mock('@/hooks/useTeams', () => ({
  useTeams: useTeamsMock,
  pickDefaultTeam: (teams: unknown[]) => (teams && teams.length > 0 ? teams[0] : null),
}))

// Partially mock @tanstack/react-router: keep createFileRoute (so the Route
// object is real and has .options), replace useNavigate to capture redirects.
const { navigateMock } = vi.hoisted(() => ({ navigateMock: vi.fn() }))
vi.mock('@tanstack/react-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-router')>()
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

const mockTeams: TeamsResponse = {
  items: [
    {
      id: 't-1',
      name: "user@example.com's Workspace",
      key: 'USER',
      issue_sequence: 0,
      created_at: '',
      updated_at: '',
      deleted_at: null,
    },
  ],
  total: 1,
  page: 1,
  size: 50,
  pages: 1,
}

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function renderWithProviders(ui: React.ReactElement) {
  const qc = makeQueryClient()
  return render(
    <QueryClientProvider client={qc}>{ui}</QueryClientProvider>,
  )
}

describe('Workspace route', () => {
  beforeEach(() => {
    useTeamsMock.mockReset()
    navigateMock.mockReset()
  })

  const Workspace = Route.options.component as React.FC

  it('navigates to /$team/issues with the default team key when teams resolve', async () => {
    useTeamsMock.mockReturnValue({
      data: mockTeams,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    })

    renderWithProviders(<Workspace />)

    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith({
        to: '/$team/issues',
        params: { team: 'USER' },
        replace: true,
      })
    })
  })

  it('shows a loading skeleton while teams are loading', () => {
    useTeamsMock.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
      refetch: vi.fn(),
    })

    renderWithProviders(<Workspace />)
    // LoadingSkeleton renders skeleton bars; navigate should NOT fire yet.
    expect(navigateMock).not.toHaveBeenCalled()
    expect(document.querySelector('[class*="animate-pulse"]')).toBeTruthy()
  })

  it('shows an error state when teams fail to load', () => {
    useTeamsMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error('Network error'),
      refetch: vi.fn(),
    })

    renderWithProviders(<Workspace />)
    expect(screen.getByText("Couldn't load your workspace")).toBeInTheDocument()
    expect(navigateMock).not.toHaveBeenCalled()
  })

  it('shows a no-workspace error when teams resolve but are empty', () => {
    useTeamsMock.mockReturnValue({
      data: { ...mockTeams, items: [], total: 0 },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    })

    renderWithProviders(<Workspace />)
    expect(screen.getByText('No workspace available')).toBeInTheDocument()
    expect(navigateMock).not.toHaveBeenCalled()
  })
})
