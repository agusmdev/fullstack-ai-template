import { Keyboard } from 'lucide-react'
import { SearchTrigger } from './SearchTrigger'
import { ThemeToggle } from './ThemeToggle'
import { UserMenu } from './UserMenu'
import { Button } from '@/components/ui/button'
import { useKeyboardShortcuts } from '@/contexts/KeyboardShortcutsContext'

/**
 * Topbar button that opens the keyboard-shortcuts help reference
 * (VAL-SHORTCUTS-007). Gives the shortcut list a permanent, discoverable entry
 * point alongside the `?` shortcut and the palette command.
 */
function ShortcutsHelpButton() {
  const { openShortcutsHelp } = useKeyboardShortcuts()
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={openShortcutsHelp}
      aria-label="Keyboard shortcuts"
      title="Keyboard shortcuts (?)"
    >
      <Keyboard className="h-4 w-4" />
    </Button>
  )
}

/**
 * Workspace topbar — Linear-style header above the main content.
 *
 * Hosts the search / command trigger (with its ⌘K hint), the keyboard-shortcuts
 * help button, the theme toggle, and the user menu (with logout). All four are
 * visible and operable.
 */
export function Topbar({ teamKey }: { teamKey?: string }) {
  return (
    <header className="flex h-12 items-center gap-2 border-b border-border bg-background px-4">
      <SearchTrigger />
      <div className="flex-1" />
      <ShortcutsHelpButton />
      <ThemeToggle />
      <UserMenu teamKey={teamKey} />
    </header>
  )
}
