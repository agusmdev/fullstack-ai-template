import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock `redirect` with a hoisted factory so we can assert on the call args
// without depending on TanStack's internal redirect encoding (which differs
// between CSR and Start/SSR runtimes).
const { redirectMock } = vi.hoisted(() => ({
  redirectMock: vi.fn((opts: unknown) => ({ __isRedirect: true, opts })),
}))

vi.mock('@tanstack/react-router', () => ({
  redirect: redirectMock,
}))

vi.mock('./auth', () => ({
  isAuthenticated: vi.fn(),
}))

import { requireAuthBeforeLoad } from './auth-guard'
import { isAuthenticated } from './auth'

describe('requireAuthBeforeLoad', () => {
  beforeEach(() => {
    redirectMock.mockClear()
    vi.mocked(isAuthenticated).mockReset()
  })

  it('redirects to /login (preserving the destination) when unauthenticated', () => {
    vi.mocked(isAuthenticated).mockReturnValue(false)

    // The guard throws the redirect object so TanStack Router can act on it.
    expect(() =>
      requireAuthBeforeLoad({ location: { pathname: '/workspace' } }),
    ).toThrow()

    expect(redirectMock).toHaveBeenCalledWith({
      to: '/login',
      search: { redirect: '/workspace' },
      replace: true,
    })
  })

  it('preserves an arbitrary deep link as the redirect target', () => {
    vi.mocked(isAuthenticated).mockReturnValue(false)

    expect(() =>
      requireAuthBeforeLoad({ location: { pathname: '/some/deep/link' } }),
    ).toThrow()

    expect(redirectMock).toHaveBeenCalledWith({
      to: '/login',
      search: { redirect: '/some/deep/link' },
      replace: true,
    })
  })

  it('does not redirect when authenticated', () => {
    vi.mocked(isAuthenticated).mockReturnValue(true)

    expect(() =>
      requireAuthBeforeLoad({ location: { pathname: '/workspace' } }),
    ).not.toThrow()
    expect(redirectMock).not.toHaveBeenCalled()
  })
})
