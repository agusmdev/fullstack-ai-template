import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render } from '@testing-library/react'
import { Route } from './_authed'

// Hoisted mocks so we can control auth state, hydration, and capture redirects.
const { navigateMock, isAuthenticatedMock, useIsHydratedMock } = vi.hoisted(() => ({
  navigateMock: vi.fn(),
  isAuthenticatedMock: vi.fn(),
  useIsHydratedMock: vi.fn(),
}))

// Partially mock @tanstack/react-router: keep createFileRoute (so the Route
// object is real and exposes .options.component), replace useNavigate.
vi.mock('@tanstack/react-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-router')>()
  return { ...actual, useNavigate: () => navigateMock }
})

vi.mock('@/lib/auth', () => ({ isAuthenticated: isAuthenticatedMock }))
vi.mock('@/hooks/useIsHydrated', () => ({ useIsHydrated: useIsHydratedMock }))
vi.mock('@/components/AppShell', () => ({
  AppShell: () => <div data-testid="app-shell">AppShell</div>,
}))
vi.mock('@/components/AppShellSkeleton', () => ({
  AppShellSkeleton: () => <div data-testid="app-shell-skeleton">AppShellSkeleton</div>,
}))

describe('_authed layout', () => {
  const AuthedLayout = Route.options.component as React.FC

  beforeEach(() => {
    navigateMock.mockReset()
    isAuthenticatedMock.mockReset()
    useIsHydratedMock.mockReset()
  })

  it('renders the neutral skeleton (not AppShell) before hydration', () => {
    useIsHydratedMock.mockReturnValue(false)
    isAuthenticatedMock.mockReturnValue(true)

    const { getByTestId, queryByTestId } = render(<AuthedLayout />)

    expect(getByTestId('app-shell-skeleton')).toBeInTheDocument()
    expect(queryByTestId('app-shell')).not.toBeInTheDocument()
    // No auth redirect during the pre-hydration frame.
    expect(navigateMock).not.toHaveBeenCalled()
  })

  it('renders AppShell after hydration when authenticated (no redirect)', () => {
    useIsHydratedMock.mockReturnValue(true)
    isAuthenticatedMock.mockReturnValue(true)

    const { getByTestId, queryByTestId } = render(<AuthedLayout />)

    expect(getByTestId('app-shell')).toBeInTheDocument()
    expect(queryByTestId('app-shell-skeleton')).not.toBeInTheDocument()
    expect(navigateMock).not.toHaveBeenCalled()
  })

  it('redirects to /login after hydration when unauthenticated (VAL-AUTH-014)', () => {
    useIsHydratedMock.mockReturnValue(true)
    isAuthenticatedMock.mockReturnValue(false)

    render(<AuthedLayout />)

    expect(navigateMock).toHaveBeenCalledWith({
      to: '/login',
      search: { redirect: window.location.pathname },
      replace: true,
    })
  })
})
