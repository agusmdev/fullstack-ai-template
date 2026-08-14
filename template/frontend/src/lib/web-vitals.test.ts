import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock the web-vitals module so we can assert initWebVitals wires each reporter.
const reporters = vi.hoisted(() => ({
  onCLS: vi.fn(),
  onINP: vi.fn(),
  onFCP: vi.fn(),
  onLCP: vi.fn(),
  onTTFB: vi.fn(),
}))

vi.mock('web-vitals', () => reporters)

describe('initWebVitals', () => {
  beforeEach(() => {
    Object.values(reporters).forEach((fn) => fn.mockClear())
  })

  it('registers all five metric reporters', async () => {
    const { initWebVitals } = await import('./web-vitals')
    initWebVitals()

    expect(reporters.onCLS).toHaveBeenCalledTimes(1)
    expect(reporters.onINP).toHaveBeenCalledTimes(1)
    expect(reporters.onFCP).toHaveBeenCalledTimes(1)
    expect(reporters.onLCP).toHaveBeenCalledTimes(1)
    expect(reporters.onTTFB).toHaveBeenCalledTimes(1)
  })

  it('passes a callback function to each reporter', async () => {
    const { initWebVitals } = await import('./web-vitals')
    initWebVitals()

    for (const fn of Object.values(reporters)) {
      const arg = fn.mock.calls[0]?.[0]
      expect(typeof arg).toBe('function')
    }
  })

  it('the registered callback logs the metric name and value when DEV is active', async () => {
    // vitest sets import.meta.env.DEV = true; only assert logging behavior in that mode.
    if (!import.meta.env.DEV) return
    const logSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

    const { initWebVitals } = await import('./web-vitals')
    initWebVitals()

    const clsCallback = reporters.onCLS.mock.calls[0][0]
    clsCallback({ name: 'CLS', value: 0.12, id: 'x' } as never)

    expect(logSpy).toHaveBeenCalledWith(
      '[Web Vitals]',
      'CLS',
      0.12,
      expect.objectContaining({ name: 'CLS', value: 0.12 }),
    )
    logSpy.mockRestore()
  })
})
