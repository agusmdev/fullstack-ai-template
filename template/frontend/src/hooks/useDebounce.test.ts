import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useDebounce } from './useDebounce'

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.runOnlyPendingTimers()
    vi.useRealTimers()
  })

  it('returns initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('hello', 300))
    expect(result.current).toBe('hello')
  })

  it('does not update before delay elapses', () => {
    const { result, rerender } = renderHook(({ value }) => useDebounce(value, 300), {
      initialProps: { value: 'initial' },
    })

    rerender({ value: 'updated' })
    vi.advanceTimersByTime(200)
    expect(result.current).toBe('initial')
  })

  it('updates after delay elapses', () => {
    const { result, rerender } = renderHook(({ value }) => useDebounce(value, 300), {
      initialProps: { value: 'initial' },
    })

    rerender({ value: 'updated' })
    act(() => {
      vi.advanceTimersByTime(300)
    })
    expect(result.current).toBe('updated')
  })

  it('resets timer on rapid updates', () => {
    const { result, rerender } = renderHook(({ value }) => useDebounce(value, 300), {
      initialProps: { value: 'a' },
    })

    rerender({ value: 'b' })
    vi.advanceTimersByTime(200)
    rerender({ value: 'c' })
    vi.advanceTimersByTime(200)
    // Still using old value since timer reset
    expect(result.current).toBe('a')

    act(() => {
      vi.advanceTimersByTime(300)
    })
    expect(result.current).toBe('c')
  })

  it('works with numbers', () => {
    const { result, rerender } = renderHook(({ value }) => useDebounce(value, 100), {
      initialProps: { value: 0 },
    })

    rerender({ value: 42 })
    act(() => {
      vi.advanceTimersByTime(100)
    })
    expect(result.current).toBe(42)
  })

  it('works with objects', () => {
    const initial = { a: 1 }
    const updated = { a: 2 }
    const { result, rerender } = renderHook(({ value }) => useDebounce(value, 100), {
      initialProps: { value: initial },
    })

    rerender({ value: updated })
    act(() => {
      vi.advanceTimersByTime(100)
    })
    expect(result.current).toEqual({ a: 2 })
  })
})
