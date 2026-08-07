import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { useNavigate } from '@tanstack/react-router'
import { useCommandPalette } from '@/contexts/CommandPaletteContext'
import { useTeamRole } from '@/hooks/useTeamRole'
import { isTypingTarget } from '@/lib/keyboard'

/**
 * Global keyboard-shortcuts provider for the authenticated workspace.
 *
 * Listens on `window` `keydown` and dispatches the M4 shortcut set:
 *
 * - `c`           → open the Create Issue dialog          (VAL-SHORTCUTS-001)
 * - `g` then `i`  → navigate to the team Issues list      (VAL-SHORTCUTS-002)
 * - `[` / `]`     → previous / next issue in the open drawer (VAL-SHORTCUTS-003)
 * - `Esc`         → close the topmost overlay              (VAL-SHORTCUTS-004)
 *   (owned by the Radix Dialog/Sheet layer — correct stacking + focus return;
 *   this provider only clears a pending `g` sequence on Escape)
 * - `⌘K`/`Ctrl+K` → toggle the command palette            (VAL-CMDK-001)
 *   (owned by `CommandPaletteProvider`; listed here for the help reference)
 * - `?`           → open this shortcuts reference          (VAL-SHORTCUTS-007)
 *
 * Single-key shortcuts are suppressed while typing in an input / textarea /
 * select / contentEditable (VAL-SHORTCUTS-005), and while a registered modal
 * overlay (the command palette, the help dialog) is open so those surfaces own
 * the keyboard.
 *
 * The provider also exposes a small registry so the Issues / Board routes can
 * publish their ordered issue list for prev/next navigation, and so modal
 * surfaces can mark themselves as "shortcut-blocking" while open.
 */

/** Ordered issue list + current selection used by `[` / `]` navigation. */
export interface IssueNav {
  ids: string[]
  currentId: string | null
  select: (id: string) => void
}

interface KeyboardShortcutsContextValue {
  /**
   * Publish the active issue-navigation context (the flattened issue order +
   * current selection). Returns an unregister function. Only one drawer is
   * open at a time; the latest registration wins.
   */
  registerIssueNav: (nav: IssueNav) => () => void
  /**
   * Mark a modal surface as open so single-key shortcuts are blocked while it
   * owns the keyboard (e.g. the command palette, the help dialog). Returns an
   * unregister function. The issue detail drawer is intentionally NOT
   * registered so `c` / `[` / `]` keep working over it.
   */
  registerOverlay: () => () => void
  /** Whether the shortcuts help reference dialog is open. */
  shortcutsHelpOpen: boolean
  openShortcutsHelp: () => void
  closeShortcutsHelp: () => void
  setShortcutsHelpOpen: (open: boolean) => void
}

const KeyboardShortcutsContext = createContext<KeyboardShortcutsContextValue | null>(null)

/** Read the keyboard-shortcuts context. Must be used inside the provider. */
export function useKeyboardShortcuts(): KeyboardShortcutsContextValue {
  const ctx = useContext(KeyboardShortcutsContext)
  if (!ctx) {
    throw new Error('useKeyboardShortcuts must be used within a KeyboardShortcutsProvider')
  }
  return ctx
}

/** How long the `g` prefix stays armed waiting for the `i` (ms). */
const G_SEQUENCE_TIMEOUT_MS = 750

export function KeyboardShortcutsProvider({
  teamKey,
  children,
}: {
  teamKey?: string
  children: ReactNode
}) {
  const { openCreateIssue } = useCommandPalette()
  const navigate = useNavigate()
  const { canWrite } = useTeamRole(teamKey)

  const [shortcutsHelpOpen, setShortcutsHelpOpen] = useState(false)
  const openShortcutsHelp = useCallback(() => setShortcutsHelpOpen(true), [])
  const closeShortcutsHelp = useCallback(() => setShortcutsHelpOpen(false), [])

  // --- Registries read by the (stable) keydown handler -------------------
  const issueNavRef = useRef<IssueNav | null>(null)
  const overlayCountRef = useRef(0)
  const gPendingRef = useRef(false)
  const gTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Latest values for the handler (avoid stale closures without re-binding).
  const canWriteRef = useRef(canWrite)
  canWriteRef.current = canWrite
  const teamKeyRef = useRef(teamKey)
  teamKeyRef.current = teamKey
  const openCreateIssueRef = useRef(openCreateIssue)
  openCreateIssueRef.current = openCreateIssue
  const openHelpRef = useRef(openShortcutsHelp)
  openHelpRef.current = openShortcutsHelp

  const registerIssueNav = useCallback((nav: IssueNav) => {
    issueNavRef.current = nav
    return () => {
      // Only clear if still ours (don't clobber a newer registration).
      if (issueNavRef.current === nav) issueNavRef.current = null
    }
  }, [])

  const registerOverlay = useCallback(() => {
    overlayCountRef.current += 1
    return () => {
      overlayCountRef.current = Math.max(0, overlayCountRef.current - 1)
    }
  }, [])

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      // Escape is handled natively by the Radix Dialog/Sheet layer, which
      // closes the topmost focus-trapped overlay with correct stacking and
      // focus return (VAL-SHORTCUTS-004). We only clear a pending `g` sequence.
      if (event.key === 'Escape') {
        gPendingRef.current = false
        return
      }

      // Modifier-key guard: any single-key shortcut combined with a modifier
      // (Cmd/Ctrl/Alt) is a native browser/OS shortcut (copy, find, browser
      // back/forward, etc.), NOT one of ours. Bail before the single-key
      // dispatch so we never preventDefault or open/spuriously trigger.
      // Without this, Cmd+C/Ctrl+C (copy) matches the `c` branch and opens
      // Create Issue while blocking native copy; Cmd+G arms the g-sequence;
      // Cmd+[ / Cmd+] hijacks browser back/forward.
      if (event.metaKey || event.ctrlKey || event.altKey) return

      const typing = isTypingTarget(event)
      const overlaysOpen = overlayCountRef.current > 0
      const key = event.key.toLowerCase()

      // Two-key sequence: `g` then `i` → go to Issues (VAL-SHORTCUTS-002).
      // Once `g` is armed, the next key is consumed by the sequence.
      if (gPendingRef.current) {
        if (gTimerRef.current) clearTimeout(gTimerRef.current)
        gPendingRef.current = false
        if (key === 'i' && !typing && !overlaysOpen && teamKeyRef.current) {
          event.preventDefault()
          navigate({ to: '/$team/issues', params: { team: teamKeyRef.current } })
        }
        return
      }

      if (key === 'g' && !typing && !overlaysOpen) {
        gPendingRef.current = true
        gTimerRef.current = setTimeout(() => {
          gPendingRef.current = false
        }, G_SEQUENCE_TIMEOUT_MS)
        return
      }

      // `c` → create issue (VAL-SHORTCUTS-001).
      if (key === 'c' && !typing && !overlaysOpen && canWriteRef.current) {
        event.preventDefault()
        openCreateIssueRef.current()
        return
      }

      // `?` → shortcuts help reference (VAL-SHORTCUTS-007).
      if (key === '?' && !typing && !overlaysOpen) {
        event.preventDefault()
        openHelpRef.current()
        return
      }

      // `[` / `]` → previous / next issue in the open drawer (VAL-SHORTCUTS-003).
      const nav = issueNavRef.current
      if (nav && !typing && !overlaysOpen) {
        const idx = nav.currentId ? nav.ids.indexOf(nav.currentId) : -1
        if (key === '[' && idx > 0) {
          event.preventDefault()
          nav.select(nav.ids[idx - 1])
        } else if (key === ']' && idx >= 0 && idx < nav.ids.length - 1) {
          event.preventDefault()
          nav.select(nav.ids[idx + 1])
        }
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [navigate])

  const value = useMemo<KeyboardShortcutsContextValue>(
    () => ({
      registerIssueNav,
      registerOverlay,
      shortcutsHelpOpen,
      openShortcutsHelp,
      closeShortcutsHelp,
      setShortcutsHelpOpen,
    }),
    [registerIssueNav, registerOverlay, shortcutsHelpOpen, openShortcutsHelp, closeShortcutsHelp],
  )

  return (
    <KeyboardShortcutsContext.Provider value={value}>
      {children}
    </KeyboardShortcutsContext.Provider>
  )
}
