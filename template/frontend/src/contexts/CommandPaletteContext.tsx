import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

/**
 * Command palette context.
 *
 * Owns the palette's open/close state and the create-action dialog states so
 * that any component (the Topbar trigger, a global shortcut, a future keyboard
 * handler) can open the palette or trigger a quick action without prop-drilling.
 *
 * The Cmd+K / Ctrl+K global shortcut is handled here (VAL-CMDK-001): toggling
 * the palette from anywhere in the authenticated workspace. Opening a create
 * action always closes the palette first so the dialog never stacks on top of
 * it (VAL-CMDK-005).
 */
interface CommandPaletteContextValue {
  /** Whether the palette dialog is currently open. */
  paletteOpen: boolean
  openPalette: () => void
  closePalette: () => void
  togglePalette: () => void
  /** Create-issue dialog open state + setters (opened from the palette). */
  createIssueOpen: boolean
  setCreateIssueOpen: (open: boolean) => void
  openCreateIssue: () => void
  /** Create-project dialog open state + setters. */
  createProjectOpen: boolean
  setCreateProjectOpen: (open: boolean) => void
  openCreateProject: () => void
  /** Create-cycle dialog open state + setters. */
  createCycleOpen: boolean
  setCreateCycleOpen: (open: boolean) => void
  openCreateCycle: () => void
}

const CommandPaletteContext = createContext<CommandPaletteContextValue | null>(null)

/**
 * Read the command palette context. Must be used inside `CommandPaletteProvider`.
 */
export function useCommandPalette(): CommandPaletteContextValue {
  const ctx = useContext(CommandPaletteContext)
  if (!ctx) {
    throw new Error('useCommandPalette must be used within a CommandPaletteProvider')
  }
  return ctx
}

export function CommandPaletteProvider({ children }: { children: ReactNode }) {
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [createIssueOpen, setCreateIssueOpen] = useState(false)
  const [createProjectOpen, setCreateProjectOpen] = useState(false)
  const [createCycleOpen, setCreateCycleOpen] = useState(false)

  const openPalette = useCallback(() => setPaletteOpen(true), [])
  const closePalette = useCallback(() => setPaletteOpen(false), [])
  const togglePalette = useCallback(() => setPaletteOpen((o) => !o), [])

  // Opening a create action always closes the palette first so the two dialogs
  // never stack (VAL-CMDK-005). Create dialogs are mutually exclusive — opening
  // one closes any other open create dialog.
  const openCreateIssue = useCallback(() => {
    setPaletteOpen(false)
    setCreateProjectOpen(false)
    setCreateCycleOpen(false)
    setCreateIssueOpen(true)
  }, [])
  const openCreateProject = useCallback(() => {
    setPaletteOpen(false)
    setCreateIssueOpen(false)
    setCreateCycleOpen(false)
    setCreateProjectOpen(true)
  }, [])
  const openCreateCycle = useCallback(() => {
    setPaletteOpen(false)
    setCreateIssueOpen(false)
    setCreateProjectOpen(false)
    setCreateCycleOpen(true)
  }, [])

  // Global Cmd+K / Ctrl+K shortcut — toggles the palette from anywhere in the
  // authenticated workspace (VAL-CMDK-001). We listen on `window` and
  // preventDefault so the browser's native search focus is not triggered.
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setPaletteOpen((o) => !o)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  const value = useMemo<CommandPaletteContextValue>(
    () => ({
      paletteOpen,
      openPalette,
      closePalette,
      togglePalette,
      createIssueOpen,
      setCreateIssueOpen,
      openCreateIssue,
      createProjectOpen,
      setCreateProjectOpen,
      openCreateProject,
      createCycleOpen,
      setCreateCycleOpen,
      openCreateCycle,
    }),
    [
      paletteOpen,
      openPalette,
      closePalette,
      togglePalette,
      createIssueOpen,
      openCreateIssue,
      createProjectOpen,
      openCreateProject,
      createCycleOpen,
      openCreateCycle,
    ],
  )

  return (
    <CommandPaletteContext.Provider value={value}>
      {children}
    </CommandPaletteContext.Provider>
  )
}
