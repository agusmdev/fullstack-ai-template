import { Outlet, useParams } from '@tanstack/react-router'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'

/**
 * Authenticated workspace shell — Sidebar + Topbar wrapping the routed page.
 *
 * Reads the current team segment (`$team`) from the URL (non-strict, so the
 * parent layout can resolve it) and threads it to the Sidebar/Topbar for team
 * identity and team-scoped navigation. Renders only behind the `_authed` guard.
 */
export function AppShell() {
  const params = useParams({ strict: false })
  const teamKey = typeof params.team === 'string' ? params.team : undefined

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
