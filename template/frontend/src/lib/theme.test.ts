import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import {
  THEME_STORAGE_KEY,
  getStoredTheme,
  setStoredTheme,
  resolveTheme,
  applyTheme,
  systemPrefersDark,
  watchSystemTheme,
} from './theme'

describe('theme storage', () => {
  beforeEach(() => localStorage.clear())

  it('getStoredTheme defaults to "system" when unset', () => {
    expect(getStoredTheme()).toBe('system')
  })

  it('setStoredTheme/getStoredTheme round-trip a mode', () => {
    setStoredTheme('dark')
    expect(getStoredTheme()).toBe('dark')
    setStoredTheme('light')
    expect(getStoredTheme()).toBe('light')
  })

  it('invalid stored values fall back to "system"', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'neon')
    expect(getStoredTheme()).toBe('system')
  })
})

describe('resolveTheme', () => {
  it('resolves explicit light/dark directly', () => {
    expect(resolveTheme('light')).toBe('light')
    expect(resolveTheme('dark')).toBe('dark')
  })

  it('"system" follows prefers-color-scheme', () => {
    const matchDark = { matches: true, media: '(prefers-color-scheme: dark)' } as MediaQueryList
    vi.stubGlobal('matchMedia', () => matchDark)
    expect(resolveTheme('system')).toBe('dark')

    const matchLight = { matches: false, media: '(prefers-color-scheme: dark)' } as MediaQueryList
    vi.stubGlobal('matchMedia', () => matchLight)
    expect(resolveTheme('system')).toBe('light')
    vi.unstubAllGlobals()
  })
})

describe('applyTheme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
  })

  it('adds the .dark class and persists for dark', () => {
    applyTheme('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(getStoredTheme()).toBe('dark')
  })

  it('removes the .dark class and persists for light', () => {
    document.documentElement.classList.add('dark')
    applyTheme('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
    expect(getStoredTheme()).toBe('light')
  })
})

describe('systemPrefersDark', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('reflects the media query matches value', () => {
    vi.stubGlobal('matchMedia', () => ({ matches: true }) as MediaQueryList)
    expect(systemPrefersDark()).toBe(true)

    vi.stubGlobal('matchMedia', () => ({ matches: false }) as MediaQueryList)
    expect(systemPrefersDark()).toBe(false)
  })
})

describe('watchSystemTheme', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('returns an unsubscribe function', () => {
    const mql = {
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    } as unknown as MediaQueryList
    vi.stubGlobal('matchMedia', () => mql)
    const unsub = watchSystemTheme(() => {})
    expect(typeof unsub).toBe('function')
    unsub()
  })
})
