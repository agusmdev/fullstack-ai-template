import { SearchTrigger } from './SearchTrigger'
import { ThemeToggle } from './ThemeToggle'
import { UserMenu } from './UserMenu'

/**
 * Workspace topbar — Linear-style header above the main content.
 *
 * Hosts the search / command trigger (M4 palette placeholder), the theme toggle,
 * and the user menu (with logout). All three are visible and operable.
 */
export function Topbar({ teamKey }: { teamKey?: string }) {
  return (
    <header className="flex h-12 items-center gap-2 border-b border-border bg-background px-4">
      <SearchTrigger />
      <div className="flex-1" />
      <ThemeToggle />
      <UserMenu teamKey={teamKey} />
    </header>
  )
}
