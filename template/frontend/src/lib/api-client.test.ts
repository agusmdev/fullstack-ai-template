import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ApiError, api } from './api-client'
import { AUTH_TOKEN_KEY } from './auth'

// --- ApiError ---

describe('ApiError', () => {
  it('creates error with status and message', () => {
    const err = new ApiError(404, 'Not found')
    expect(err.status).toBe(404)
    expect(err.message).toBe('Not found')
    expect(err.name).toBe('ApiError')
  })

  it('stores optional code', () => {
    const err = new ApiError(422, 'Validation failed', 'validation_error')
    expect(err.code).toBe('validation_error')
  })

  it('stores optional fields', () => {
    const fields = { email: ['Invalid email'], password: ['Too short'] }
    const err = new ApiError(422, 'Validation failed', 'validation_error', fields)
    expect(err.fields).toEqual(fields)
  })

  it('is instance of Error', () => {
    const err = new ApiError(500, 'Server error')
    expect(err instanceof Error).toBe(true)
  })

  it('is instance of ApiError', () => {
    const err = new ApiError(401, 'Unauthorized')
    expect(err instanceof ApiError).toBe(true)
  })

  it('has undefined code when not provided', () => {
    const err = new ApiError(404, 'Not found')
    expect(err.code).toBeUndefined()
  })

  it('has undefined fields when not provided', () => {
    const err = new ApiError(404, 'Not found')
    expect(err.fields).toBeUndefined()
  })
})

// --- ApiClient.request() HTTP behavior ---

function mockFetch(status: number, body?: unknown, ok = status >= 200 && status < 300) {
  const response = {
    ok,
    status,
    json: body !== undefined
      ? vi.fn().mockResolvedValue(body)
      : vi.fn().mockRejectedValue(new Error('No body')),
  }
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))
  return response
}

describe('ApiClient.request()', () => {
  beforeEach(() => {
    localStorage.clear()
    // Reset window.location.href tracking
    vi.stubGlobal('location', { href: '' })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('injects Bearer token when one is stored', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'my-token')
    mockFetch(200, { id: '1' })

    await api.get('/test')

    const fetchMock = vi.mocked(fetch)
    const headers = (fetchMock.mock.calls[0][1] as RequestInit).headers as Record<string, string>
    expect(headers['Authorization']).toBe('Bearer my-token')
  })

  it('omits Authorization header when no token is stored', async () => {
    mockFetch(200, { id: '1' })

    await api.get('/test')

    const fetchMock = vi.mocked(fetch)
    const headers = (fetchMock.mock.calls[0][1] as RequestInit).headers as Record<string, string>
    expect(headers['Authorization']).toBeUndefined()
  })

  it('returns parsed JSON on a successful 200 response', async () => {
    mockFetch(200, { name: 'hello' })

    const result = await api.get<{ name: string }>('/test')

    expect(result).toEqual({ name: 'hello' })
  })

  it('returns undefined on a 204 No Content response', async () => {
    const response = { ok: true, status: 204, json: vi.fn() }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))

    const result = await api.delete('/test')

    expect(result).toBeUndefined()
    expect(response.json).not.toHaveBeenCalled()
  })

  it('clears token and redirects to /login on 401', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'expired-token')
    const response = { ok: false, status: 401, json: vi.fn().mockResolvedValue({}) }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))

    await expect(api.get('/protected')).rejects.toThrow(ApiError)
    expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBeNull()
    expect(window.location.href).toBe('/login')
  })

  it('throws ApiError with parsed detail on non-ok response', async () => {
    mockFetch(404, { detail: 'Not found', code: 'not_found' }, false)

    await expect(api.get('/missing')).rejects.toMatchObject({
      status: 404,
      message: 'Not found',
      code: 'not_found',
    })
  })

  it('falls back to HTTP status message when error JSON has no detail', async () => {
    mockFetch(500, {}, false)

    await expect(api.get('/error')).rejects.toMatchObject({
      status: 500,
      message: 'HTTP 500',
    })
  })

  it('falls back gracefully when error response body is not valid JSON', async () => {
    const response = {
      ok: false,
      status: 503,
      json: vi.fn().mockRejectedValue(new SyntaxError('Unexpected token')),
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))

    await expect(api.get('/broken')).rejects.toMatchObject({
      status: 503,
      message: 'HTTP 503',
    })
  })

  it('throws ApiError with field errors on validation failure', async () => {
    mockFetch(422, {
      detail: 'Validation failed',
      code: 'validation_error',
      fields: { email: ['Invalid email'] },
    }, false)

    await expect(api.post('/items', {})).rejects.toMatchObject({
      status: 422,
      fields: { email: ['Invalid email'] },
    })
  })
})
