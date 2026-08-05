import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { executeAuthSubmit } from './useAuthSubmit'
import type { AuthSessionResponse } from '@/types/auth'

const mockSession: AuthSessionResponse = {
  id: 'session-token-123',
  expires_at: '2099-01-01T00:00:00Z',
  expires_in: 3600,
}

// Mock sonner so we can assert on toast calls, and error-handler so we can
// assert the error path is wired correctly without depending on its internals.
const toastMock = vi.hoisted(() => ({ success: vi.fn(), error: vi.fn() }))
const errorHandlerMock = vi.hoisted(() => ({ toastApiError: vi.fn() }))

vi.mock('sonner', () => ({ toast: toastMock }))
vi.mock('@/lib/error-handler', () => ({ toastApiError: errorHandlerMock.toastApiError }))

function mockFetch(status: number, body?: unknown) {
  const response = {
    ok: status >= 200 && status < 300,
    status,
    json:
      body !== undefined
        ? vi.fn().mockResolvedValue(body)
        : vi.fn().mockRejectedValue(new Error('No body')),
  }
  const spy = vi.fn().mockResolvedValue(response)
  vi.stubGlobal('fetch', spy)
  return spy
}

describe('executeAuthSubmit', () => {
  const login = vi.fn()
  const navigate = vi.fn()
  const successMessage = 'Signed in'
  const errorMessage = 'Login failed'
  const redirect = { to: '/' as const }

  beforeEach(() => {
    login.mockReset()
    navigate.mockReset()
    toastMock.success.mockReset()
    toastMock.error.mockReset()
    errorHandlerMock.toastApiError.mockReset()
    localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('calls login() with the session token on success', async () => {
    mockFetch(200, mockSession)

    await executeAuthSubmit('/auth/login', { email: 'a@b.com', password: 'pw' }, {
      login,
      navigate,
      successMessage,
      errorMessage,
      redirect,
    })

    expect(login).toHaveBeenCalledWith(mockSession.id)
  })

  it('calls navigate() with the redirect option on success', async () => {
    mockFetch(200, mockSession)

    await executeAuthSubmit('/auth/login', {}, { login, navigate, successMessage, errorMessage, redirect })

    expect(navigate).toHaveBeenCalledWith(redirect)
  })

  it('posts the payload as JSON to the configured endpoint', async () => {
    const fetchSpy = mockFetch(200, mockSession)

    await executeAuthSubmit('/auth/login', { email: 'a@b.com', password: 'pw' }, {
      login,
      navigate,
      successMessage,
      errorMessage,
      redirect,
    })

    expect(fetchSpy).toHaveBeenCalledWith(
      'http://localhost:9095/auth/login',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ email: 'a@b.com', password: 'pw' }),
      }),
    )
  })

  it('shows the success toast on success', async () => {
    mockFetch(200, mockSession)

    await executeAuthSubmit('/auth/login', {}, { login, navigate, successMessage, errorMessage, redirect })

    expect(toastMock.success).toHaveBeenCalledWith(successMessage)
  })

  it('does not call login or navigate on API error', async () => {
    mockFetch(401, { detail: 'Unauthorized' })

    await executeAuthSubmit('/auth/login', {}, { login, navigate, successMessage, errorMessage, redirect })

    expect(login).not.toHaveBeenCalled()
    expect(navigate).not.toHaveBeenCalled()
  })

  it('routes the error through toastApiError with the fallback message', async () => {
    mockFetch(400, { detail: 'Invalid credentials' })

    await executeAuthSubmit('/auth/login', {}, { login, navigate, successMessage, errorMessage, redirect })

    expect(errorHandlerMock.toastApiError).toHaveBeenCalledTimes(1)
    const [err, message] = errorHandlerMock.toastApiError.mock.calls[0]
    expect(message).toBe(errorMessage)
    // The error surfaced is an ApiError carrying the API detail.
    expect(err).toBeInstanceOf(Error)
    expect((err as Error).message).toBe('Invalid credentials')
  })

  it('does not show a success toast on error', async () => {
    mockFetch(500, {})

    await executeAuthSubmit('/auth/login', {}, { login, navigate, successMessage, errorMessage, redirect })

    expect(toastMock.success).not.toHaveBeenCalled()
  })

  it('swallows network errors without throwing (handled by toastApiError)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Network down')))

    await expect(
      executeAuthSubmit('/auth/login', {}, { login, navigate, successMessage, errorMessage, redirect }),
    ).resolves.toBeUndefined()

    expect(errorHandlerMock.toastApiError).toHaveBeenCalledTimes(1)
    expect(login).not.toHaveBeenCalled()
  })
})
