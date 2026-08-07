import { useState } from 'react'
import { createFileRoute, useParams } from '@tanstack/react-router'
import { Plus, Inbox, SearchX } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { IssueBoard } from '@/components/IssueBoard'
import { IssueBoardSkeleton } from '@/components/IssueBoardSkeleton'
import { IssueFiltersBar } from '@/components/IssueFiltersBar'
import { ViewToggle } from '@/components/ViewToggle'
import { CreateIssueDialog } from '@/components/CreateIssueDialog'
import { IssueDetailDrawer } from '@/components/IssueDetailDrawer'
import { useTeams } from '@/hooks/useTeams'
import { useUser } from '@/hooks/useUser'
import { useTeamRole } from '@/hooks/useTeamRole'
import { useIssues, flattenIssues, issuesTotal, useUpdateIssue } from '@/hooks/useIssues'
import { useIssueFilters } from '@/hooks/useIssueFilters'
import { useWorkflowStates } from '@/hooks/useWorkflowStates'
import { useLabels } from '@/hooks/useLabels'
import { useProjects } from '@/hooks/useProjects'
import { useCycles } from '@/hooks/useCycles'
import { validateIssueSearch } from '@/lib/issue-search'
import { toastApiError } from '@/lib/error-handler'
import type { Issue } from '@/types/issue'

/**
 * Board view — the kanban board, one column per workflow status ordered by
 * `position` (VAL-BOARD-001).
 *
 * - Cards show identifier, title, priority, assignee, labels (VAL-BOARD-002).
 * - Drag-and-drop a card between columns changes its status optimistically +
 *   persists via PATCH; rolls back on failure (VAL-BOARD-003, VAL-BOARD-008).
 *   The non-DnD move path is the detail drawer's status picker (VAL-BOARD-004).
 * - The filter bar + list↔board toggle share URL search params with the Issues
 *   list, so toggling preserves scope + filters (VAL-BOARD-005, VAL-BOARD-006).
 * - Empty columns are valid drop targets (VAL-BOARD-007).
 * - Board ↔ list ↔ detail status consistency via shared React Query cache
 *   (VAL-BOARD-009, VAL-BOARD-010).
 */
export const Route = createFileRoute('/_authed/$team/board')({
  validateSearch: validateIssueSearch,
  component: BoardView,
})

function BoardView() {
  const { team: teamKey } = useParams({ strict: false })
  const [createOpen, setCreateOpen] = useState(false)
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null)

  const urlSearch = Route.useSearch()
  const { params: queryParams, searchInput, setSearchInput, setParams, clear, hasActive, urlSearch: rawSearch } =
    useIssueFilters(urlSearch)

  const { data: teamsData, isLoading: teamsLoading } = useTeams()
  const { data: user } = useUser()
  const { canWrite } = useTeamRole(teamKey)

  const teamObj = (teamsData?.items ?? []).find((t) => t.key === teamKey)
  const teamId = teamObj?.id

  const issuesQuery = useIssues(teamId, queryParams)
  const statesQuery = useWorkflowStates(teamId)
  const labelsQuery = useLabels(teamId)
  const projectsQuery = useProjects(teamId)
  const cyclesQuery = useCycles(teamId)

  const updateIssue = useUpdateIssue()

  const workflowStates = statesQuery.data?.items ?? []
  const labels = labelsQuery.data?.items ?? []
  const projects = projectsQuery.data?.items ?? []
  const cycles = cyclesQuery.data?.items ?? []
  const issues = flattenIssues(issuesQuery.data)
  const total = issuesTotal(issuesQuery.data)

  const members = user
    ? [{ id: user.id, name: user.display_name || user.email }]
    : []
  const assigneeNames: Record<string, string> = Object.fromEntries(
    members.map((m) => [m.id, m.name]),
  )

  const initialLoading =
    teamsLoading || (teamId ? issuesQuery.isLoading || statesQuery.isLoading : true)

  /**
   * DnD drop handler: change the issue's status optimistically via
   * `useUpdateIssue`. The hook patches `status_id` in every list cache variant
   * (so the card moves column instantly) and rolls back on failure
   * (VAL-BOARD-003, VAL-BOARD-008).
   *
   * No-op when the target column is the same as the source (avoids a pointless
   * PATCH).
   */
  const handleMoveIssue = (issueId: string, targetStatusId: string) => {
    if (!teamId) return
    const issue = issues.find((i) => i.id === issueId)
    if (!issue || issue.status_id === targetStatusId) return
    updateIssue.mutate(
      { id: issueId, team_id: teamId, status_id: targetStatusId },
      {
        onError: (error) => {
          // The hook already rolls back the cache + shows a toast; this extra
          // surface is for any board-specific error handling.
          toastApiError(error, 'Failed to move issue')
        },
      },
    )
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-6 py-3">
        <div className="flex items-center gap-3">
          <h1 className="text-base font-semibold text-foreground">Board</h1>
          <ViewToggle teamKey={teamKey ?? ''} active="board" search={rawSearch} />
        </div>
        <Button
          size="sm"
          onClick={() => setCreateOpen(true)}
          disabled={!canWrite}
          title={canWrite ? undefined : 'Guests have read-only access to this team'}
        >
          <Plus className="h-4 w-4" />
          New issue
        </Button>
      </div>

      {/* Filter bar — shared with the Issues list via URL search params */}
      {!initialLoading && (total > 0 || hasActive) && (
        <div className="border-b border-border px-6 py-2.5">
          <IssueFiltersBar
            params={queryParams}
            searchInput={searchInput}
            onSearchInputChange={setSearchInput}
            onParamsChange={setParams}
            onClear={clear}
            hasActive={hasActive}
            workflowStates={workflowStates}
            labels={labels}
            members={members}
          />
        </div>
      )}

      {/* Body */}
      <div className="flex-1 overflow-hidden p-4">
        {initialLoading ? (
          <IssueBoardSkeleton columns={Math.min(workflowStates.length || 4, 5)} />
        ) : issuesQuery.isError ? (
          <ErrorState
            error={issuesQuery.error}
            onRetry={() => issuesQuery.refetch()}
            title="Couldn't load board"
          />
        ) : total === 0 ? (
          hasActive ? (
            <EmptyState
              icon={SearchX}
              title="No matching issues"
              description="No issues match the current filters. Try adjusting or clearing them."
              action={
                <Button size="sm" variant="outline" onClick={clear}>
                  Clear filters
                </Button>
              }
            />
          ) : (
            <EmptyState
              icon={Inbox}
              title="No issues yet"
              description="Create your first issue to see it on the board."
              action={
                canWrite ? (
                  <Button size="sm" onClick={() => setCreateOpen(true)}>
                    <Plus className="h-4 w-4" />
                    Create issue
                  </Button>
                ) : (
                  <p className="text-xs text-muted-foreground">
                    Guests have read-only access to this team.
                  </p>
                )
              }
            />
          )
        ) : (
          <IssueBoard
            issues={issues}
            workflowStates={workflowStates}
            assigneeNames={assigneeNames}
            onSelectIssue={setSelectedIssue}
            onMoveIssue={handleMoveIssue}
          />
        )}
      </div>

      <CreateIssueDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        teamId={teamId ?? ''}
        workflowStates={workflowStates}
        labels={labels}
        members={members}
      />

      {/* Detail drawer — status picker here is the non-DnD move path */}
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
