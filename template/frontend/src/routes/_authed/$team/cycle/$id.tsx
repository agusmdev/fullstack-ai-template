import { useMemo, useState } from 'react'
import { createFileRoute, useParams, Link } from '@tanstack/react-router'
import { ArrowLeft, Repeat2, Inbox, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { IssueList } from '@/components/IssueList'
import { IssueListSkeleton } from '@/components/IssueListSkeleton'
import { IssueDetailDrawer } from '@/components/IssueDetailDrawer'
import { useTeams } from '@/hooks/useTeams'
import { useUser } from '@/hooks/useUser'
import { useCycle, useCycles } from '@/hooks/useCycles'
import { useIssues, flattenIssues, issuesTotal } from '@/hooks/useIssues'
import { useWorkflowStates } from '@/hooks/useWorkflowStates'
import { useLabels } from '@/hooks/useLabels'
import { useProjects } from '@/hooks/useProjects'
import {
  cyclePhase,
  formatCycleWindow,
  computeCycleProgress,
} from '@/types/cycle'
import { DEFAULT_SORT_KEY, type Issue } from '@/types/issue'

export const Route = createFileRoute('/_authed/$team/cycle/$id')({
  component: CycleDetailView,
})

const PHASE_STYLES: Record<string, string> = {
  active: 'bg-primary/10 text-primary',
  upcoming: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
  past: 'bg-muted text-muted-foreground',
}

/**
 * Cycle detail view — shows the cycle header (name, date window, phase) and
 * lists **only** that cycle's issues (filtered server-side by ``cycle_id``)
 * with a progress indicator derived from terminal statuses (VAL-CYCLES-004,
 * VAL-CYCLES-006).
 *
 * Issues assigned from the drawer appear here within invalidation/polling and
 * persist on reload. The cycle picker in the drawer is the assign/remove
 * surface (VAL-CYCLES-005).
 */
function CycleDetailView() {
  const { team: teamKey, id: cycleId } = useParams({ strict: false })
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null)

  const { data: teamsData, isLoading: teamsLoading } = useTeams()
  const { data: user } = useUser()
  const teamObj = (teamsData?.items ?? []).find((t) => t.key === teamKey)
  const teamId = teamObj?.id

  const cycleQuery = useCycle(cycleId)
  const statesQuery = useWorkflowStates(teamId)
  const labelsQuery = useLabels(teamId)
  const cyclesQuery = useCycles(teamId)
  const projectsQuery = useProjects(teamId)
  // Fetch only this cycle's issues (server-side cycle_id filter).
  const issuesQuery = useIssues(teamId, {
    cycle_id: cycleId,
    sort: DEFAULT_SORT_KEY,
  })

  const cycle = cycleQuery.data
  const workflowStates = statesQuery.data?.items ?? []
  const labels = labelsQuery.data?.items ?? []
  const cycles = cyclesQuery.data?.items ?? []
  const projects = projectsQuery.data?.items ?? []
  const issues = flattenIssues(issuesQuery.data)
  const total = issuesTotal(issuesQuery.data)

  const members = user
    ? [{ id: user.id, name: user.display_name || user.email }]
    : []
  const assigneeNames: Record<string, string> = Object.fromEntries(
    members.map((m) => [m.id, m.name]),
  )
  const projectNames: Record<string, string> = Object.fromEntries(
    projects.map((p) => [p.id, p.name]),
  )

  // Lookup of status_id → workflow state type (for progress computation).
  const workflowStateTypes = useMemo(() => {
    const m = new Map<string, string>()
    for (const s of workflowStates) m.set(s.id, s.type)
    return m
  }, [workflowStates])

  const progress = useMemo(
    () => computeCycleProgress(issues, workflowStateTypes),
    [issues, workflowStateTypes],
  )

  const initialLoading = teamsLoading || (teamId ? cycleQuery.isLoading : true)

  if (initialLoading) {
    return (
      <div className="flex items-center gap-2 p-6 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading cycle…
      </div>
    )
  }

  if (cycleQuery.isError || !cycle) {
    return (
      <div className="p-6">
        <ErrorState
          error={cycleQuery.error ?? new Error('Cycle not found')}
          title="Cycle not found"
        />
        <div className="mt-3 flex justify-center">
          <Button asChild variant="outline" size="sm">
            <Link to="/$team/cycles" params={{ team: teamKey ?? '' }}>
              <ArrowLeft className="h-4 w-4" />
              Back to cycles
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  const phase = cyclePhase(cycle)
  const progressPct = progress.total > 0 ? (progress.done / progress.total) * 100 : 0

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-border px-6 py-3">
        <div className="mb-2 flex items-center gap-2">
          <Button asChild variant="ghost" size="sm" className="h-7 gap-1 px-2 text-muted-foreground">
            <Link to="/$team/cycles" params={{ team: teamKey ?? '' }}>
              <ArrowLeft className="h-3.5 w-3.5" />
              Cycles
            </Link>
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Repeat2 className="h-4 w-4 text-muted-foreground" />
          <h1 className="text-lg font-semibold text-foreground">{cycle.name}</h1>
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] uppercase ${
              PHASE_STYLES[phase] ?? 'bg-muted text-muted-foreground'
            }`}
          >
            {phase}
          </span>
        </div>
        <div className="mt-1 flex items-center gap-4 text-xs text-muted-foreground">
          <span>{formatCycleWindow(cycle)}</span>
          <span>{total} issue{total === 1 ? '' : 's'}</span>
        </div>

        {/* Progress bar (VAL-CYCLES-006) */}
        {progress.total > 0 && (
          <div className="mt-2 max-w-xs">
            <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
              <span>Progress</span>
              <span>{progress.done} of {progress.total} done</span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-primary transition-all"
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Body — only this cycle's issues (VAL-CYCLES-004) */}
      <div className="flex-1 overflow-auto p-6">
        {statesQuery.isLoading ? (
          <IssueListSkeleton groups={Math.min(workflowStates.length || 3, 5)} />
        ) : issuesQuery.isError ? (
          <ErrorState
            error={issuesQuery.error}
            onRetry={() => issuesQuery.refetch()}
            title="Couldn't load issues"
          />
        ) : total === 0 ? (
          <EmptyState
            icon={Inbox}
            title="No issues in this cycle"
            description="Assign issues to this cycle from the issue drawer to see them here."
          />
        ) : (
          <IssueList
            issues={issues}
            workflowStates={workflowStates}
            assigneeNames={assigneeNames}
            projectNames={projectNames}
            onSelectIssue={setSelectedIssue}
          />
        )}
      </div>

      <IssueDetailDrawer
        open={!!selectedIssue}
        onOpenChange={(o) => !o && setSelectedIssue(null)}
        issueId={selectedIssue?.id ?? null}
        initialIssue={selectedIssue ?? undefined}
        teamId={teamId ?? ''}
        workflowStates={workflowStates}
        labels={labels}
        projects={projects}
        cycles={cycles}
        members={members}
      />
    </div>
  )
}
