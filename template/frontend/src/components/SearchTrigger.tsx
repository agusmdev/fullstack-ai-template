import { Search } from 'lucide-react'
import { useCommandPalette } from '@/contexts/CommandPaletteContext'

/**
 * Topbar search / command-palette trigger — a visible, operable affordance.
 *
 * Clicking it opens the Cmd+K command palette (VAL-CMDK-002). The keyboard hint
 * ("⌘K") advertises the global shortcut handled by `CommandPaletteProvider`.
 */
export function SearchTrigger() {
  const { openPalette } = useCommandPalette()

  return (
    <button
      type="button"
      onClick={openPalette}
      className="inline-flex h-8 items-center gap-2 rounded-md border border-border bg-muted/40 px-3 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      aria-label="Search and run commands"
    >
      <Search className="h-4 w-4" />
      <span className="hidden sm:inline">Search…</span>
      <kbd className="ml-1 hidden rounded border border-border bg-background px-1.5 text-[10px] font-medium text-muted-foreground sm:inline">
        ⌘K
      </kbd>
    </button>
  )
}
