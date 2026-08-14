import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React, { type ReactNode } from 'react'
import { useAuthSubmit } from './useAuthSubmit'

// The hook composes useNavigate() + useAuth() + the executeAuthSubmit orchestrator.
// We mock each collaborator to verify the wiring (endpoint/payload/deps passthrough,
// the isLoading lifecycle, error propagation) and to confirm the hook performs no
// direct side effects — every effect flows through executeAuthSubmit.
const navigateMock = vi.fn()
const loginMock = vi.fn()
const executeMock = vi.hoisted(() => vi.fn())

vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => navigateMock,
}))
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ login: loginMock }),
}))
vi.mock('@/features/auth/auth-actions', () => ({
  executeAuthSubmit: executeMock,
}))

function wrapper({ children }: { children: ReactNode }) {
  // useMutation requires a QueryClient context; create a fresh client per
  // render so onSuccess invalidation has no cross-test cache leakage.
  const queryClient = new QueryClient({ defaultOptions: { mutations: { retry: false } } })
  return React.createElement(QueryClientProvider, { client: queryClient }, children)
}

describe('useAuthSubmit', () => {
  beforeEach(() => {
    navigateMock.mockReset()
    loginMock.mockReset()
    executeMock.mockReset()
    executeMock.mockResolvedValue(undefined)
  })

  it('exposes a stable { submit, isLoading } surface with isLoading initially false', () => {
    const { result } = renderHook(
      () => useAuthSubmit('/auth/login', 'Signed in', 'Login failed'),
      { wrapper },
    )

    expect(result.current.isLoading).toBe(false)
    expect(typeof result.current.submit).toBe('function')
    // Only these two keys are part of the public contract — nothing else leaks.
    expect(Object.keys(result.current).sort()).toEqual(['isLoading', 'submit'])
  })

  it('delegates to executeAuthSubmit exactly once per submit, forwarding the endpoint verbatim', async () => {
    const { result } = renderHook(
      () => useAuthSubmit('/auth/register', 'Welcome', 'Registration failed'),
      { wrapper },
    )

    await act(async () => {
      await result.current.submit({ email: 'a@b.com' })
    })

    expect(executeMock).toHaveBeenCalledTimes(1)
    const [endpoint] = executeMock.mock.calls[0]
    expect(endpoint).toBe('/auth/register')
    expect(typeof endpoint).toBe('string')
  })

  it('forwards the payload by reference without cloning or mutating it', async () => {
    const { result } = renderHook(
      () => useAuthSubmit('/auth/login', 'Signed in', 'Login failed'),
      { wrapper },
    )
    const payload = { email: 'a@b.com', password: 'pw', remember: true }

    await act(async () => {
      await result.current.submit(payload)
    })

    const [, passedPayload] = executeMock.mock.calls[0]
    expect(passedPayload).toBe(payload)
    expect(passedPayload).toEqual({ email: 'a@b.com', password: 'pw', remember: true })
  })

  it('assembles a deps bag with exactly login, navigate, successMessage, errorMessage, and redirect', async () => {
    const { result } = renderHook(
      () => useAuthSubmit('/auth/login', 'Signed in', 'Login failed'),
      { wrapper },
    )

    await act(async () => {
      await result.current.submit({})
    })

    const [, , deps] = executeMock.mock.calls[0]
    expect(Object.keys(deps).sort()).toEqual(
      ['errorMessage', 'login', 'navigate', 'redirect', 'successMessage'],
    )
    expect(deps).toMatchObject({
      login: loginMock,
      navigate: navigateMock,
      successMessage: 'Signed in',
      errorMessage: 'Login failed',
    })
  })

  it('defaults the redirect to { to: "/" } when the caller omits it', async () => {
    const { result } = renderHook(
      () => useAuthSubmit('/auth/login', 'Signed in', 'Login failed'),
      { wrapper },
    )

    await act(async () => {
      await result.current.submit({})
    })

    expect(executeMock.mock.calls[0][2].redirect).toEqual({ to: '/' })
  })

  it('passes a caller-provided redirect through untouched', async () => {
    const customRedirect = { to: '/items' as const }
    const { result } = renderHook(
      () => useAuthSubmit('/auth/login', 'Signed in', 'Login failed', customRedirect),
      { wrapper },
    )

    await act(async () => {
      await result.current.submit({})
    })

    const { redirect } = executeMock.mock.calls[0][2]
    expect(redirect).toBe(customRedirect)
    expect(redirect).toEqual({ to: '/items' })
  })

  it('sets isLoading true before the orchestrator runs and false after it resolves', async () => {
    let resolveSubmit!: () => void
    executeMock.mockReturnValue(new Promise<void>((resolve) => { resolveSubmit = resolve }))

    const { result } = renderHook(
      () => useAuthSubmit('/auth/login', 'Signed in', 'Login failed'),
      { wrapper },
    )

    expect(result.current.isLoading).toBe(false)

    let pending!: Promise<void>
    act(() => {
      pending = result.current.submit({})
    })
    // Loading flips on synchronously, before the orchestrator's await yields.
    await waitFor(() => expect(result.current.isLoading).toBe(true))
    expect(executeMock).toHaveBeenCalledTimes(1)

    await act(async () => {
      resolveSubmit()
      await pending
    })
    // isPending flips back to false on the post-resolution re-render, which
    // commits after mutateAsync resolves; waitFor lets that update flush.
    await waitFor(() => expect(result.current.isLoading).toBe(false))
  })

  it('resets isLoading to false when the orchestrator rejects, and resolves without rethrowing', async () => {
    // The orchestrator already surfaces the failure (toast); submit must not
    // reject, or react-hook-form's handleSubmit turns every failed login into
    // an unhandled promise rejection.
    const boom = new Error('boom')
    executeMock.mockRejectedValue(boom)

    const { result } = renderHook(
      () => useAuthSubmit('/auth/login', 'Signed in', 'Login failed'),
      { wrapper },
    )

    await act(async () => {
      await expect(result.current.submit({})).resolves.toBeUndefined()
    })

    expect(result.current.isLoading).toBe(false)
    expect(executeMock).toHaveBeenCalledTimes(1)
  })

  it('never calls login or navigate directly — all side effects flow through the orchestrator', async () => {
    const { result } = renderHook(
      () => useAuthSubmit('/auth/login', 'Signed in', 'Login failed'),
      { wrapper },
    )

    await act(async () => {
      await result.current.submit({})
    })

    expect(loginMock).not.toHaveBeenCalled()
    expect(navigateMock).not.toHaveBeenCalled()
  })

  it('supports successive submits, toggling isLoading through each cycle in order', async () => {
    const { result } = renderHook(
      () => useAuthSubmit('/auth/login', 'Signed in', 'Login failed'),
      { wrapper },
    )

    for (let i = 0; i < 3; i++) {
      await act(async () => {
        await result.current.submit({ n: i })
      })
      expect(result.current.isLoading).toBe(false)
    }

    expect(executeMock).toHaveBeenCalledTimes(3)
    expect(executeMock.mock.calls.map((c) => (c[1] as { n: number }).n)).toEqual([0, 1, 2])
  })

  it('treats the success and error messages as opaque strings (no interpolation)', async () => {
    const { result } = renderHook(
      () => useAuthSubmit('/auth/login', 'Welcome back, user!', 'Login failed: try again'),
      { wrapper },
    )

    await act(async () => {
      await result.current.submit({})
    })

    const { successMessage, errorMessage } = executeMock.mock.calls[0][2]
    expect(successMessage).toBe('Welcome back, user!')
    expect(errorMessage).toBe('Login failed: try again')
  })
})
