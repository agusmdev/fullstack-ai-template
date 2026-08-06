import { Link } from '@tanstack/react-router'
import { Inbox, LayoutGrid, Folder, Repeat2, Eye, Bookmark, ChevronsUpDown } from 'lucide-react'
import { useTeams } from '@/hooks/useTeams'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

interface NavItem {
  label: string
  icon: React.ComponentType<{ className?: string }>
  to: '/$team/issues' | '/$team/board' | '/$team/projects' | '/$team/cycles' | '/$team/views'
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Issues', icon: Inbox, to: '/$team/issues' },
  { label: 'Board', icon: LayoutGrid, to: '/$team/board' },
  { label: 'Projects', icon: Folder, to: '/$team/projects' },
  { label: 'Cycles', icon: Repeat2, to: '/$team/cycles' },
  { label: 'Views', icon: Eye, to: '/$team/views' },
]

/**
 * Workspace sidebar — Linear-style left rail.
 *
 * Renders the active team identity (name + key) at the top, the primary
 * navigation (Issues / Board / Projects / Cycles / Views), and a saved-views
 * area (empty for M0; populated by the Views feature in M3). Navigation uses
 * TanStack <Link> so entries route without a full page reload, and the active
 * entry is highlighted via `activeProps`.
 */
export function Sidebar({ teamKey }: { teamKey?: string }) {
  const { data, isLoading } = useTeams()
  const teams = data?.items ?? []
  const current = teams.find((t) => t.key === teamKey) ?? teams[0]
  const activeKey = teamKey ?? current?.key

  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-border bg-card md:flex">
      {/* Team identity */}
      <div className="flex items-center gap-2 border-b border-border px-3 py-3">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary/10 text-xs font-bold text-primary">
          {(current?.key ?? '?').slice(0, 2)}
        </div>
        <div className="min-w-0 flex-1">
          {isLoading ? (
            <Skeleton className="h-4 w-28" />
          ) : (
            <p className="truncate text-sm font-semibold text-foreground">
              {current?.name ?? 'Workspace'}
            </p>
          )}
          {activeKey && (
            <p className="text-xs text-muted-foreground">{activeKey}</p>
          )}
        </div>
        <ChevronsUpDown className="h-4 w-4 text-muted-foreground" />
      </div>

      {/* Primary navigation */}
      <nav className="flex flex-col gap-0.5 px-2 py-3" aria-label="Workspace navigation">
        {NAV_ITEMS.map(({ label, icon: Icon, to }) => (
          <Link
            key={to}
            to={to}
            params={{ team: activeKey ?? '' }}
            className={cn(
              'flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm font-medium text-muted-foreground no-underline transition-colors hover:bg-accent hover:text-foreground',
            )}
            activeProps={{ className: 'bg-accent text-foreground' }}
            activeOptions={{ exact: false }}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </nav>

      {/* Saved views (M0 placeholder) */}
      <div className="mt-2 flex-1 border-t border-border px-2 py-3">
        <p className="px-2 pb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground/70">
          Views
        </p>
        <div className="flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm text-muted-foreground/60">
          <Bookmark className="h-4 w-4" />
          No saved views
        </div>
      </div>
    </aside>
  )
}
