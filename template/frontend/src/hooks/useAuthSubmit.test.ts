import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import React, { type ReactNode } from 'react'
import { useAuthSubmit } from './useAuthSubmit'

// The hook composes useNavigate() + useAuth() + the executeAuthSubmit orchestrator.
// We mock each collaborator to verify the wiring (endpoint/messages/redirect passthrough,
// isLoading lifecycle) without performing real HTTP or router navigation.
const navigateMock = vi.fn()
const loginMock = vi.fn()
const executeMock = vi.hoisted(() => vi.fn())

vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => navigateMock,
}))
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ login: loginMock }),
}))
vi.mock('@/lib/auth-actions', () => ({
  executeAuthSubmit: executeMock,
}))

function wrapper({ children }: { children: ReactNode }) {
  return React.createElement(React.Fragment, null, children)
}

describe('useAuthSubmit', () => {
  beforeEach(() => {
    navigateMock.mockReset()
    loginMock.mockReset()
    executeMock.mockReset()
  })

  it('exposes submit and isLoading (initially false)', () => {
    const { result } = renderHook(
      () => useAuthSubmit('/auth/login', 'Signed in', 'Login failed'),
      { wrapper },
    )

    expect(result.current.isLoading).toBe(false)
    expect(typeof result.current.submit).toBe('function')
  })

  it('defaults the redirect to the home route', async () => {
    executeMock.mockResolvedValue(undefined)
    const { result } = renderHook(
      () => useAuthSubmit('/auth/login', 'Signed in', 'Login failed'),
      { wrapper },
    )

    await act(async () => {
      await result.current.submit({ email: 'a@b.com', password: 'pw' })
    })

    expect(executeMock).toHaveBeenCalledTimes(1)
    const [, , deps] = executeMock.mock.calls[0]
    expect(deps).toMatchObject({
      login: loginMock,
      navigate: navigateMock,
      successMessage: 'Signed in',
      errorMessage: 'Login failed',
      redirect: { to: '/' },
    })
  })

  it('honors a caller-provided redirect', async () => {
    executeMock.mockResolvedValue(undefined)
    const { result } = renderHook(
      () =>
        useAuthSubmit('/auth/register', 'Welcome', 'Registration failed', {
          to: '/items',
        }),
      { wrapper },
    )

    await act(async () => {
      await result.current.submit({ email: 'a@b.com', password: 'pw' })
    })

    const [endpoint, , deps] = executeMock.mock.calls[0]
    expect(endpoint).toBe('/auth/register')
    expect(deps.redirect).toEqual({ to: '/items' })
  })

  it('forwards the submit payload as the orchestrator payload', async () => {
    executeMock.mockResolvedValue(undefined)
    const { result } = renderHook(
      () => useAuthSubmit('/auth/login', 'Signed in', 'Login failed'),
      { wrapper },
    )
    const payload = { email: 'a@b.com', password: 'pw' }

    await act(async () => {
      await result.current.submit(payload)
    })

    const [, passedPayload] = executeMock.mock.calls[0]
    expect(passedPayload).toBe(payload)
  })

  it('toggles isLoading true while submitting, then back to false on success', async () => {
    let resolveSubmit!: () => void
    executeMock.mockReturnValue(new Promise<void>((resolve) => { resolveSubmit = resolve }))

    const { result } = renderHook(
      () => useAuthSubmit('/auth/login', 'Signed in', 'Login failed'),
      { wrapper },
    )

    expect(result.current.isLoading).toBe(false)
    let pending: Promise<void>
    act(() => {
      pending = result.current.submit({})
    })
    await waitFor(() => expect(result.current.isLoading).toBe(true))

    await act(async () => {
      resolveSubmit()
      await pending!
    })
    expect(result.current.isLoading).toBe(false)
  })

  it('resets isLoading to false even when the orchestrator rejects', async () => {
    executeMock.mockRejectedValue(new Error('boom'))

    const { result } = renderHook(
      () => useAuthSubmit('/auth/login', 'Signed in', 'Login failed'),
      { wrapper },
    )

    await act(async () => {
      await expect(result.current.submit({})).rejects.toThrow('boom')
    })

    expect(result.current.isLoading).toBe(false)
  })
})
