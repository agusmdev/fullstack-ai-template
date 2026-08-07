import { createFileRoute, useParams } from '@tanstack/react-router'
import { Plus, Lock } from 'lucide-react'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { StatusDot } from '@/components/StatusDot'
import { useUser } from '@/hooks/useUser'
import { useTeams } from '@/hooks/useTeams'
import { useTeamRole } from '@/hooks/useTeamRole'
import { useWorkflowStates } from '@/hooks/useWorkflowStates'

/**
 * Settings view — profile + theme preferences + team workflow states.
 *
 * Reachable from the topbar user menu (VAL-CROSS-005). The theme toggle here is
 * the same control as in the topbar; it persists across reload and logout/login.
 *
 * The **Workflow states** section is an admin-only management surface: every
 * member can read the team's statuses, but only admins may mutate them — the
 * "Add state" control is disabled for members/guests with an explicit
 * "Admin only" hint (VAL-CROSS-025).
 */
export const Route = createFileRoute('/_authed/$team/settings')({
  component: SettingsView,
})

function SettingsView() {
  const { team: teamKey } = useParams({ strict: false })
  const { data: user } = useUser()
  const { data: teamsData } = useTeams()
  const teamId = (teamsData?.items ?? []).find((t) => t.key === teamKey)?.id
  const { canAdmin } = useTeamRole(teamKey)
  const statesQuery = useWorkflowStates(teamId)

  const states = statesQuery.data?.items ?? []

  return (
    <div className="p-6">
      <h1 className="mb-6 text-lg font-semibold text-foreground">Settings</h1>

      <section className="max-w-xl space-y-6">
        <div className="rounded-lg border border-border p-4">
          <h2 className="mb-1 text-sm font-medium text-foreground">Profile</h2>
          <p className="mb-3 text-sm text-muted-foreground">
            Your account details.
          </p>
          <dl className="space-y-1 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Name</dt>
              <dd className="text-foreground">{user?.display_name ?? '—'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Email</dt>
              <dd className="text-foreground">{user?.email ?? '—'}</dd>
            </div>
          </dl>
        </div>

        <div className="flex items-center justify-between rounded-lg border border-border p-4">
          <div>
            <h2 className="mb-1 text-sm font-medium text-foreground">Appearance</h2>
            <p className="text-sm text-muted-foreground">
              Choose light, dark, or system. Persists across reload and login.
            </p>
          </div>
          <div className="shrink-0">
            <ThemeToggle />
          </div>
        </div>

        {/* Workflow states — admin-only management (reads for all). */}
        <div className="rounded-lg border border-border p-4">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-medium text-foreground">Workflow states</h2>
              <p className="text-sm text-muted-foreground">
                The statuses issues can be in for this team.
              </p>
            </div>
            <Button
              size="sm"
              variant="outline"
              disabled={!canAdmin}
              title={canAdmin ? undefined : 'Only team admins can manage workflow states'}
            >
              <Plus className="h-4 w-4" />
              Add state
            </Button>
          </div>

          {statesQuery.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-6 w-full" />
              ))}
            </div>
          ) : states.length === 0 ? (
            <p className="text-sm text-muted-foreground">No workflow states.</p>
          ) : (
            <ul className="space-y-1">
              {states.map((s) => (
                <li
                  key={s.id}
                  className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm text-foreground"
                >
                  <StatusDot type={s.type} />
                  <span>{s.name}</span>
                  <span className="text-xs text-muted-foreground">({s.type})</span>
                </li>
              ))}
            </ul>
          )}

          {!canAdmin && (
            <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
              <Lock className="h-3 w-3" />
              Admin only — you can view workflow states but not change them.
            </p>
          )}
        </div>
      </section>
    </div>
  )
}
