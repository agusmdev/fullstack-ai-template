import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { executeAuthSubmit } from './auth-actions'
import { ApiError } from './api-client'
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
  const baseDeps = { login, navigate, successMessage, errorMessage, redirect }

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

    await executeAuthSubmit('/auth/login', { email: 'a@b.com', password: 'pw' }, baseDeps)

    expect(login).toHaveBeenCalledTimes(1)
    expect(login).toHaveBeenCalledWith(mockSession.id)
    expect(login).toHaveBeenCalledWith(expect.stringMatching(/^session-token-/))
  })

  it('calls navigate() with the redirect option on success', async () => {
    mockFetch(200, mockSession)

    await executeAuthSubmit('/auth/login', {}, baseDeps)

    expect(navigate).toHaveBeenCalledTimes(1)
    expect(navigate).toHaveBeenCalledWith(redirect)
    expect(navigate).toHaveBeenCalledWith({ to: '/' })
  })

  it('posts the payload as JSON to the configured endpoint with POST method', async () => {
    const fetchSpy = mockFetch(200, mockSession)
    const payload = { email: 'a@b.com', password: 'pw' }

    await executeAuthSubmit('/auth/login', payload, baseDeps)

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    expect(fetchSpy).toHaveBeenCalledWith(
      'http://localhost:9095/auth/login',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(payload),
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
      }),
    )
  })

  it('shows the success toast (and only the success toast) on success', async () => {
    mockFetch(200, mockSession)

    await executeAuthSubmit('/auth/login', {}, baseDeps)

    expect(toastMock.success).toHaveBeenCalledTimes(1)
    expect(toastMock.success).toHaveBeenCalledWith(successMessage)
    expect(toastMock.error).not.toHaveBeenCalled()
    expect(errorHandlerMock.toastApiError).not.toHaveBeenCalled()
  })

  it('does not call login, navigate, or success toast on API error', async () => {
    mockFetch(401, { detail: 'Unauthorized' })

    await executeAuthSubmit('/auth/login', {}, baseDeps)

    expect(login).not.toHaveBeenCalled()
    expect(navigate).not.toHaveBeenCalled()
    expect(toastMock.success).not.toHaveBeenCalled()
  })

  it('routes the error through toastApiError with the fallback message and a typed ApiError', async () => {
    mockFetch(400, { detail: 'Invalid credentials' })

    await executeAuthSubmit('/auth/login', {}, baseDeps)

    expect(errorHandlerMock.toastApiError).toHaveBeenCalledTimes(1)
    const [err, message] = errorHandlerMock.toastApiError.mock.calls[0]
    expect(message).toBe(errorMessage)
    expect(err).toBeInstanceOf(ApiError)
    expect((err as ApiError).status).toBe(400)
    expect((err as ApiError).message).toBe('Invalid credentials')
  })

  it('passes the API-provided code and fields through to the surfaced ApiError', async () => {
    mockFetch(422, {
      detail: 'Validation failed',
      code: 'VALIDATION_ERROR',
      fields: { email: ['Invalid'] },
    })

    await executeAuthSubmit('/auth/register', {}, baseDeps)

    const [err] = errorHandlerMock.toastApiError.mock.calls[0]
    expect(err).toBeInstanceOf(ApiError)
    expect((err as ApiError).code).toBe('VALIDATION_ERROR')
    expect((err as ApiError).fields).toEqual({ email: ['Invalid'] })
  })

  it('does not show a success toast on a 500 error', async () => {
    mockFetch(500, {})

    await executeAuthSubmit('/auth/login', {}, baseDeps)

    expect(toastMock.success).not.toHaveBeenCalled()
    expect(errorHandlerMock.toastApiError).toHaveBeenCalledTimes(1)
  })

  it('swallows network errors without throwing (handled by toastApiError)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Network down')))

    await expect(
      executeAuthSubmit('/auth/login', {}, baseDeps),
    ).resolves.toBeUndefined()

    expect(errorHandlerMock.toastApiError).toHaveBeenCalledTimes(1)
    expect(login).not.toHaveBeenCalled()
    expect(navigate).not.toHaveBeenCalled()
    expect(toastMock.success).not.toHaveBeenCalled()
  })

  it('honors a custom redirect target separate from the default', async () => {
    mockFetch(200, mockSession)
    const customRedirect = { to: '/items' as const }

    await executeAuthSubmit('/auth/login', {}, { ...baseDeps, redirect: customRedirect })

    expect(navigate).toHaveBeenCalledWith(customRedirect)
    expect(navigate).not.toHaveBeenCalledWith(redirect)
  })
})
