import { useState } from 'react'
import { createFileRoute, useParams, Link } from '@tanstack/react-router'
import { Plus, Repeat2, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { CycleFormDialog } from '@/components/CycleFormDialog'
import { useTeams } from '@/hooks/useTeams'
import { useTeamRole } from '@/hooks/useTeamRole'
import { useCycles } from '@/hooks/useCycles'
import {
  cyclePhase,
  formatCycleWindow,
  type Cycle,
} from '@/types/cycle'

export const Route = createFileRoute('/_authed/$team/cycles')({
  component: CyclesView,
})

const PHASE_STYLES: Record<string, string> = {
  active: 'bg-primary/10 text-primary',
  upcoming: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
  past: 'bg-muted text-muted-foreground',
}

/**
 * Cycles view — the team-scoped cycles list.
 *
 * - Shows every cycle in the team with its date window and phase
 *   (past/active/upcoming) badge (VAL-CYCLES-008).
 * - Empty state with a "New Cycle" CTA when there are no cycles
 *   (VAL-CYCLES-003).
 * - Create-cycle dialog (name + start + end required; end > start validated)
 *   (VAL-CYCLES-001, VAL-CYCLES-002).
 * - Each cycle links to its detail view.
 */
function CyclesView() {
  const { team: teamKey } = useParams({ strict: false })
  const [createOpen, setCreateOpen] = useState(false)

  const { data: teamsData, isLoading: teamsLoading } = useTeams()
  const { canWrite } = useTeamRole(teamKey)

  const teamObj = (teamsData?.items ?? []).find((t) => t.key === teamKey)
  const teamId = teamObj?.id

  const cyclesQuery = useCycles(teamId)
  const cycles = cyclesQuery.data?.items ?? []
  const total = cyclesQuery.data?.total ?? 0

  const initialLoading = teamsLoading || (teamId ? cyclesQuery.isLoading : true)

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-6 py-3">
        <h1 className="text-base font-semibold text-foreground">Cycles</h1>
        <Button size="sm" onClick={() => setCreateOpen(true)} disabled={!canWrite}>
          <Plus className="h-4 w-4" />
          New cycle
        </Button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-auto p-6">
        {initialLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading cycles…
          </div>
        ) : cyclesQuery.isError ? (
          <ErrorState
            error={cyclesQuery.error}
            onRetry={() => cyclesQuery.refetch()}
            title="Couldn't load cycles"
          />
        ) : total === 0 ? (
          <EmptyState
            icon={Repeat2}
            title="No cycles yet"
            description="Time-box your work into sprints. Create a cycle to start tracking progress toward a deadline."
            action={
              canWrite ? (
                <Button size="sm" onClick={() => setCreateOpen(true)}>
                  <Plus className="h-4 w-4" />
                  New cycle
                </Button>
              ) : (
                <p className="text-xs text-muted-foreground">
                  Guests have read-only access to this team.
                </p>
              )
            }
          />
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {cycles.map((cycle: Cycle) => {
              const phase = cyclePhase(cycle)
              return (
                <Link
                  key={cycle.id}
                  to="/$team/cycle/$id"
                  params={{ team: teamKey ?? '', id: cycle.id }}
                  className="flex flex-col gap-2 rounded-lg border border-border bg-card p-4 no-underline transition-colors hover:bg-accent/50"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="text-sm font-semibold text-foreground">
                      {cycle.name}
                    </h3>
                    <span
                      className={`inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[11px] uppercase ${
                        PHASE_STYLES[phase] ?? 'bg-muted text-muted-foreground'
                      }`}
                    >
                      {phase}
                    </span>
                  </div>
                  <div className="mt-auto flex items-center gap-2 pt-2 text-xs text-muted-foreground">
                    <Repeat2 className="h-3 w-3" />
                    <span>{formatCycleWindow(cycle)}</span>
                  </div>
                </Link>
              )
            })}
          </div>
        )}
      </div>

      <CycleFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        teamId={teamId ?? ''}
      />
    </div>
  )
}
