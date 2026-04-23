import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { executeAuthSubmit } from './useAuthSubmit'
import type { AuthSessionResponse } from '@/types/auth'

const mockSession: AuthSessionResponse = { id: 'session-token-123', expires_at: '2099-01-01T00:00:00Z', expires_in: 3600 }

function mockFetch(status: number, body?: unknown) {
  const response = {
    ok: status >= 200 && status < 300,
    status,
    json: body !== undefined
      ? vi.fn().mockResolvedValue(body)
      : vi.fn().mockRejectedValue(new Error('No body')),
  }
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))
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
    localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('calls login() with the session token on success', async () => {
    mockFetch(200, mockSession)

    await executeAuthSubmit('/auth/login', { email: 'a@b.com', password: 'pw' }, {
      login, navigate, successMessage, errorMessage, redirect,
    })

    expect(login).toHaveBeenCalledWith(mockSession.id)
  })

  it('calls navigate() with the redirect option on success', async () => {
    mockFetch(200, mockSession)

    await executeAuthSubmit('/auth/login', {}, { login, navigate, successMessage, errorMessage, redirect })

    expect(navigate).toHaveBeenCalledWith(redirect)
  })

  it('does not call login or navigate on API error', async () => {
    mockFetch(401, { detail: 'Unauthorized' })

    await executeAuthSubmit('/auth/login', {}, { login, navigate, successMessage, errorMessage, redirect })

    expect(login).not.toHaveBeenCalled()
    expect(navigate).not.toHaveBeenCalled()
  })
})
