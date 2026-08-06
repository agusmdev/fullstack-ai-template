import { Outlet, useParams } from '@tanstack/react-router'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'
import { useTeamAccessGuard } from '@/hooks/useTeamAccessGuard'

/**
 * Authenticated workspace shell — Sidebar + Topbar wrapping the routed page.
 *
 * Reads the current team segment (`$team`) from the URL (non-strict, so the
 * parent layout can resolve it) and threads it to the Sidebar/Topbar for team
 * identity and team-scoped navigation. Renders only behind the `_authed` guard.
 *
 * Also enforces the SPA-side cross-team guard: if the URL's team segment is not
 * one of the user's teams, the user is redirected to their default team so no
 * foreign team's data is ever rendered (VAL-CROSS-024).
 */
export function AppShell() {
  const params = useParams({ strict: false })
  const teamKey = typeof params.team === 'string' ? params.team : undefined
  useTeamAccessGuard(teamKey)

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      <Sidebar teamKey={teamKey} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar teamKey={teamKey} />
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
