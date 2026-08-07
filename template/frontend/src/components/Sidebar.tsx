import { Link, useNavigate } from '@tanstack/react-router'
import { Inbox, LayoutGrid, Folder, Repeat2, Eye, ChevronsUpDown, Check } from 'lucide-react'
import { useTeams } from '@/hooks/useTeams'
import { SavedViews } from '@/components/SavedViews'
import { Skeleton } from '@/components/ui/skeleton'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown'
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
 * Renders the active team identity (name + key) at the top as a **team
 * switcher** (VAL-CROSS-009): a dropdown listing every team the user belongs to;
 * selecting one navigates to that team's issues view, which re-scopes all
 * team-keyed queries (no cross-team data leak). The primary navigation
 * (Issues / Board / Projects / Cycles / Views) and a saved-views area follow.
 * Navigation uses TanStack <Link> so entries route without a full page reload,
 * and the active entry is highlighted via `activeProps`.
 */
export function Sidebar({ teamKey }: { teamKey?: string }) {
  const { data, isLoading } = useTeams()
  const navigate = useNavigate()
  const teams = data?.items ?? []
  const current = teams.find((t) => t.key === teamKey) ?? teams[0]
  const activeKey = teamKey ?? current?.key

  const switchTeam = (key: string) => {
    // Re-scope to the chosen team's issues view. Routes + queries are keyed by
    // the team segment, so React Query refetches the new team's data and the
    // old team's data is never rendered.
    void navigate({ to: '/$team/issues', params: { team: key } })
  }

  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-border bg-card md:flex">
      {/* Team identity + switcher */}
      <DropdownMenu>
        <DropdownMenuTrigger>
          <button
            type="button"
            className="flex w-full items-center gap-2 border-b border-border px-3 py-3 text-left transition-colors hover:bg-accent"
            aria-label="Switch team"
          >
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
            <ChevronsUpDown className="h-4 w-4 shrink-0 text-muted-foreground" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-56" align="start">
          <DropdownMenuLabel>Your teams</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {teams.map((t) => (
            <DropdownMenuItem
              key={t.id}
              onClick={() => switchTeam(t.key)}
              className="justify-between"
            >
              <span className="flex min-w-0 items-center gap-2">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-primary/10 text-[10px] font-bold text-primary">
                  {t.key.slice(0, 2)}
                </span>
                <span className="truncate">{t.name}</span>
              </span>
              {t.key === activeKey && <Check className="h-4 w-4 shrink-0 text-primary" />}
            </DropdownMenuItem>
          ))}
          {teams.length === 0 && !isLoading && (
            <div className="px-2 py-1.5 text-sm text-muted-foreground">No teams</div>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

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

      {/* Saved views (M3) */}
      <SavedViews teamKey={activeKey} teamId={current?.id} />
    </aside>
  )
}
