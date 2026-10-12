import { getConfig } from './config'
import { getAuthToken, clearAuthToken } from './auth'

interface ValidationIssue {
  loc: (string | number)[]
  msg: string
}

// Backend error body: `{ detail, error_code }`. FastAPI request validation (422)
// sends `detail` as a list of issues instead of a string.
interface ApiErrorBody {
  detail?: string | ValidationIssue[]
  error_code?: string
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    /** The backend's `error_code` (e.g. `duplicate_item`), or a client code such as `network_error`. */
    public code?: string,
    /** Field name → messages, for request validation errors (422). */
    public fields?: Record<string, string[]>
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

const SESSION_EXPIRED_MESSAGE = 'Your session has expired. Please sign in again.'

function toFieldErrors(issues: ValidationIssue[]): Record<string, string[]> {
  const fields: Record<string, string[]> = {}
  for (const { loc, msg } of issues) {
    const field = String(loc.at(-1))
    fields[field] = [...(fields[field] ?? []), msg]
  }
  return fields
}

async function readErrorBody(response: Response): Promise<ApiErrorBody | null> {
  try {
    const body: unknown = await response.json()
    return body && typeof body === 'object' ? (body as ApiErrorBody) : null
  } catch {
    return null
  }
}

function toApiError(status: number, body: ApiErrorBody | null): ApiError {
  if (!body) return new ApiError(status, `HTTP ${status}`, 'invalid_error_body')
  const { detail, error_code } = body
  if (Array.isArray(detail)) {
    const fields = toFieldErrors(detail)
    const message = Object.entries(fields)
      .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
      .join('; ')
    return new ApiError(
      status,
      message || 'Validation failed',
      error_code ?? 'validation_error',
      fields
    )
  }
  const message = typeof detail === 'string' && detail ? detail : `HTTP ${status}`
  return new ApiError(status, message, error_code)
}

/**
 * True when the backend refused the request for lack of a valid session:
 * - 401 for a token it does not accept (expired, revoked, unknown);
 * - 403 "Not authenticated" from FastAPI's HTTPBearer when no token was sent,
 *   e.g. the user signed out in another tab while this one stayed open.
 * A 401 without a token (wrong password on /auth/login) is a normal error.
 */
function isRejectedSession(status: number, body: ApiErrorBody | null, sentToken: boolean) {
  if (status === 401) return sentToken
  return status === 403 && body?.detail === 'Not authenticated'
}

class ApiClient {
  private get baseUrl() {
    return getConfig().apiBaseUrl
  }

  // Executes the request with auth and error handling; returns the raw Response.
  private async execute(endpoint: string, options?: RequestInit): Promise<Response> {
    const token = getAuthToken()
    // Resolve outside the try: baseUrl runs env validation, and a config error
    // must not be re-labeled as a network failure by the catch below.
    const url = `${this.baseUrl}${endpoint}`

    let response: Response
    try {
      response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
          ...options?.headers,
        },
      })
    } catch {
      // Network-level failure (DNS, offline, CORS, blocked): fetch rejects with a
      // raw TypeError. Normalize it into the app's ApiError so callers never see
      // an unstructured network error leak through.
      throw new ApiError(0, 'Network request failed', 'network_error')
    }

    if (!response.ok) {
      const body = await readErrorBody(response)
      if (isRejectedSession(response.status, body, token !== null)) {
        // Drop the dead session: AuthProvider clears the cached data, and pages
        // in routes/_authed/ send the user to /login. The message is fixed
        // because the backend's detail is meant for developers.
        clearAuthToken()
        throw new ApiError(response.status, SESSION_EXPIRED_MESSAGE, body?.error_code)
      }
      throw toApiError(response.status, body)
    }

    return response
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return (await this.execute(endpoint, options)).json()
  }

  get<T>(endpoint: string) {
    return this.request<T>(endpoint)
  }

  post<T>(endpoint: string, data: unknown) {
    return this.request<T>(endpoint, { method: 'POST', body: JSON.stringify(data) })
  }

  put<T>(endpoint: string, data: unknown) {
    return this.request<T>(endpoint, { method: 'PUT', body: JSON.stringify(data) })
  }

  patch<T>(endpoint: string, data: unknown) {
    return this.request<T>(endpoint, { method: 'PATCH', body: JSON.stringify(data) })
  }

  delete(endpoint: string): Promise<void> {
    // execute() validates auth/errors; we discard the body (204 No Content returns nothing).
    return this.execute(endpoint, { method: 'DELETE' }).then(() => undefined)
  }
}

export const api = new ApiClient()
