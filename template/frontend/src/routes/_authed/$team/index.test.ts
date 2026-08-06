import { describe, it, expect, vi } from 'vitest'

// Partially mock @tanstack/react-router: keep createFileRoute (so the Route
// object is real), replace redirect to capture the call args.
const { redirectMock } = vi.hoisted(() => ({
  redirectMock: vi.fn((opts: unknown) => ({ __isRedirect: true, opts })),
}))

vi.mock('@tanstack/react-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-router')>()
  return {
    ...actual,
    redirect: redirectMock,
  }
})

import { Route } from './index'

describe('/$team/ index route', () => {
  const beforeLoad = Route.options.beforeLoad as unknown as (ctx: {
    params: { team: string }
  }) => void

  it('redirects to /$team/issues with the team param', () => {
    expect(() => beforeLoad({ params: { team: 'ENG' } })).toThrow()

    expect(redirectMock).toHaveBeenCalledWith({
      to: '/$team/issues',
      params: { team: 'ENG' },
      replace: true,
    })
  })

  it('preserves an arbitrary team key in the redirect', () => {
    redirectMock.mockClear()

    expect(() => beforeLoad({ params: { team: 'DESIGN' } })).toThrow()

    expect(redirectMock).toHaveBeenCalledWith({
      to: '/$team/issues',
      params: { team: 'DESIGN' },
      replace: true,
    })
  })
})
