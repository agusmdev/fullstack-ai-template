import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { getConfig } from './config'

describe('getConfig', () => {
  const originalEnv = { ...import.meta.env }

  beforeEach(() => {
    vi.resetModules()
  })

  afterEach(() => {
    // Restore import.meta.env
    vi.stubGlobal('__restore', undefined)
    Object.assign(import.meta.env, originalEnv)
  })

  it('defaults apiBaseUrl to http://localhost:9095 when the env var is unset', () => {
    delete (import.meta.env as Record<string, unknown>).VITE_API_BASE_URL
    const config = getConfig()
    expect(config.apiBaseUrl).toBe('http://localhost:9095')
  })

  it('uses the VITE_API_BASE_URL value when provided', () => {
    import.meta.env.VITE_API_BASE_URL = 'https://api.example.com'
    const config = getConfig()
    expect(config.apiBaseUrl).toBe('https://api.example.com')
  })

  it('rejects an invalid (non-url) value', () => {
    import.meta.env.VITE_API_BASE_URL = 'not-a-url'
    expect(() => getConfig()).toThrow()
  })
})
