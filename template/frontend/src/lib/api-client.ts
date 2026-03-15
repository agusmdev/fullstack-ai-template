import { getConfig } from './config'
import { getAuthToken, clearAuthToken } from './auth'

interface ApiErrorResponse {
  detail: string
  code?: string
  fields?: Record<string, string[]>
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string,
    public fields?: Record<string, string[]>
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

class ApiClient {
  private get baseUrl() { return getConfig().apiBaseUrl }

  // Executes the request with auth and error handling; returns the raw Response.
  private async execute(endpoint: string, options?: RequestInit): Promise<Response> {
    const token = getAuthToken()

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options?.headers,
      },
    })

    if (response.status === 401) {
      clearAuthToken()
      throw new ApiError(401, 'Session expired')
    }

    if (!response.ok) {
      const data = await response.json().catch(() => ({})) as ApiErrorResponse
      throw new ApiError(
        response.status,
        data.detail || `HTTP ${response.status}`,
        data.code,
        data.fields
      )
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
