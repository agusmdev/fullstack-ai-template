/**
 * Theme system — light / dark / system, persisted in localStorage and applied
 * to <html> as a `.dark` class before first paint (no flash).
 *
 * The selected mode lives in localStorage under `THEME_STORAGE_KEY` and survives
 * reload and logout/login (it is independent of the auth token). "system" tracks
 * the OS `prefers-color-scheme` media query and updates live.
 */

export type ThemeMode = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'

export const THEME_STORAGE_KEY = 'theme'

const VALID_MODES: ReadonlySet<ThemeMode> = new Set(['light', 'dark', 'system'])

const DARK_CLASS = 'dark'

/** True when running in a browser with matchMedia available. */
function hasMedia(): boolean {
  return typeof window !== 'undefined' && typeof window.matchMedia === 'function'
}

/** True when the OS prefers a dark color scheme. */
export function systemPrefersDark(): boolean {
  return hasMedia() && window.matchMedia('(prefers-color-scheme: dark)').matches
}

/** Resolve a stored mode to the concrete theme that should be rendered. */
export function resolveTheme(mode: ThemeMode): ResolvedTheme {
  if (mode === 'system') return systemPrefersDark() ? 'dark' : 'light'
  return mode
}

/** Read the stored theme mode, falling back to "system". Invalid values default to system. */
export function getStoredTheme(): ThemeMode {
  if (typeof localStorage === 'undefined') return 'system'
  const raw = localStorage.getItem(THEME_STORAGE_KEY)
  if (raw && VALID_MODES.has(raw as ThemeMode)) return raw as ThemeMode
  return 'system'
}

/** Persist the theme mode to localStorage (no-op on the server). */
export function setStoredTheme(mode: ThemeMode): void {
  if (typeof localStorage === 'undefined') return
  localStorage.setItem(THEME_STORAGE_KEY, mode)
}

/** Toggle the `.dark` class on <html> for the given resolved theme. */
function applyDarkClass(resolved: ResolvedTheme): void {
  if (typeof document === 'undefined') return
  document.documentElement.classList.toggle(DARK_CLASS, resolved === 'dark')
}

/**
 * Apply a theme mode: persist it, resolve it, and toggle the `.dark` class
 * immediately. Used by the ThemeToggle on user interaction.
 */
export function applyTheme(mode: ThemeMode): void {
  setStoredTheme(mode)
  applyDarkClass(resolveTheme(mode))
}

/**
 * Subscribe to OS color-scheme changes while in "system" mode, re-applying the
 * resolved theme. Returns an unsubscribe function.
 *
 * Only meaningful in "system" mode; other modes ignore the media query.
 */
export function watchSystemTheme(onChange: (resolved: ResolvedTheme) => void): () => void {
  if (!hasMedia()) return () => {}
  const mql = window.matchMedia('(prefers-color-scheme: dark)')
  const handler = (e: MediaQueryListEvent) => {
    if (getStoredTheme() !== 'system') return
    const resolved: ResolvedTheme = e.matches ? 'dark' : 'light'
    applyDarkClass(resolved)
    onChange(resolved)
  }
  mql.addEventListener('change', handler)
  return () => mql.removeEventListener('change', handler)
}
