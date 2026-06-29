import { describe, it, expect, vi, beforeEach } from 'vitest'
import { logger } from './logger'

describe('logger', () => {
  beforeEach(() => {
    vi.spyOn(console, 'debug').mockImplementation(() => {})
    vi.spyOn(console, 'info').mockImplementation(() => {})
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  it('should call console.info for info level', () => {
    logger.info('test message')
    expect(console.info).toHaveBeenCalledTimes(1)
  })

  it('should call console.warn for warn level', () => {
    logger.warn('warning message')
    expect(console.warn).toHaveBeenCalledTimes(1)
  })

  it('should call console.error for error level', () => {
    logger.error('error message')
    expect(console.error).toHaveBeenCalledTimes(1)
  })

  it('should redact sensitive keys in context', () => {
    logger.info('login attempt', { password: 'secret123', email: 'test@test.com' })
    const call = vi.mocked(console.info).mock.calls[0][0] as Record<string, unknown>
    expect(call.password).toBe('[REDACTED]')
    expect(call.email).toBe('test@test.com')
  })
})
