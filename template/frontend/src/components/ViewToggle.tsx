import { List, LayoutGrid } from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { cn } from '@/lib/utils'
import type { IssueUrlSearch } from '@/lib/issue-search'

interface ViewToggleProps {
  /** The current team key (route param). */
  teamKey: string
  /** Which view is active: 'list' or 'board'. */
  active: 'list' | 'board'
  /** Current URL search params (filters) to carry across the toggle. */
  search: IssueUrlSearch
}

/**
 * Segmented List ↔ Board toggle.
 *
 * Uses TanStack `<Link>` to navigate between `/$team/issues` and `/$team/board`,
 * carrying the **same** search params (filters) so the underlying issue set is
 * preserved — only the presentation changes (VAL-BOARD-005).
 */
export function ViewToggle({ teamKey, active, search }: ViewToggleProps) {
  const baseClass =
    'inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors no-underline'

  return (
    <div className="inline-flex items-center gap-0.5 rounded-lg border border-border bg-muted/40 p-0.5">
      <Link
        to="/$team/issues"
        params={{ team: teamKey }}
        search={search}
        className={cn(
          baseClass,
          active === 'list'
            ? 'bg-background text-foreground shadow-sm'
            : 'text-muted-foreground hover:text-foreground',
        )}
        aria-current={active === 'list' ? 'page' : undefined}
        aria-label="List view"
      >
        <List className="h-3.5 w-3.5" />
        List
      </Link>
      <Link
        to="/$team/board"
        params={{ team: teamKey }}
        search={search}
        className={cn(
          baseClass,
          active === 'board'
            ? 'bg-background text-foreground shadow-sm'
            : 'text-muted-foreground hover:text-foreground',
        )}
        aria-current={active === 'board' ? 'page' : undefined}
        aria-label="Board view"
      >
        <LayoutGrid className="h-3.5 w-3.5" />
        Board
      </Link>
    </div>
  )
}
