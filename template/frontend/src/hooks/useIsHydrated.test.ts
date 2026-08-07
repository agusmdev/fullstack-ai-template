import { describe, it, expect } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useIsHydrated } from './useIsHydrated'

describe('useIsHydrated', () => {
  it('is false on the initial render and true after mount', () => {
    // Capture every rendered value via the render callback so we can observe
    // the pre-effect (initial) value, which RTL's renderHook otherwise hides
    // because it flushes mount effects before returning.
    const values: boolean[] = []
    const { result } = renderHook(() => {
      const isHydrated = useIsHydrated()
      values.push(isHydrated)
      return isHydrated
    })

    expect(values[0]).toBe(false) // initial render (hydration frame)
    expect(result.current).toBe(true) // after the mount effect flushes
  })

  it('stays true across subsequent renders', () => {
    const { result, rerender } = renderHook(() => useIsHydrated())
    expect(result.current).toBe(true)
    rerender()
    expect(result.current).toBe(true)
  })
})
