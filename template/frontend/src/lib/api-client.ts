import { config } from './config'
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
  private get baseUrl() { return config.apiBaseUrl }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
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
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
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

    if (response.status === 204) {
      // 204 No Content — callers on this path must use Promise<void> (e.g. delete())
      return undefined as unknown as T
    }

    return response.json()
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
    return this.request<void>(endpoint, { method: 'DELETE' })
  }
}

export const api = new ApiClient()
