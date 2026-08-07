/**
 * Keyboard-shortcut helpers (pure, testable).
 *
 * Centralises the "is the user typing in a text field?" check used to suppress
 * single-key shortcuts (VAL-SHORTCUTS-005) and the canonical shortcut
 * definitions surfaced in the help reference and inline hints
 * (VAL-SHORTCUTS-006/007).
 */

/** A key combination + human description shown in the shortcuts reference. */
export interface ShortcutDef {
  /** Display label for the keys, e.g. "⌘K", "G I", "C". */
  keys: string
  /** What the shortcut does. */
  description: string
}

/** Grouped shortcut definitions powering the help reference (VAL-SHORTCUTS-007). */
export const SHORTCUT_GROUPS: { heading: string; items: ShortcutDef[] }[] = [
  {
    heading: 'General',
    items: [
      { keys: '⌘K', description: 'Open command palette' },
      { keys: '?', description: 'Open this shortcuts reference' },
      { keys: 'Esc', description: 'Close dialog or drawer' },
    ],
  },
  {
    heading: 'Navigation',
    items: [
      { keys: 'G I', description: 'Go to Issues' },
      { keys: '[', description: 'Previous issue (in drawer)' },
      { keys: ']', description: 'Next issue (in drawer)' },
    ],
  },
  {
    heading: 'Actions',
    items: [{ keys: 'C', description: 'Create issue' }],
  },
]

/**
 * Determine whether a keyboard event originated from a text-editing element
 * (input, textarea, select, or contentEditable). Single-key global shortcuts
 * are suppressed in this case so the character is typed normally
 * (VAL-SHORTCUTS-005).
 */
export function isTypingTarget(event: KeyboardEvent): boolean {
  const target = event.target
  if (!(target instanceof HTMLElement)) return false
  const tag = target.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true
  if (target.isContentEditable) return true
  return false
}
