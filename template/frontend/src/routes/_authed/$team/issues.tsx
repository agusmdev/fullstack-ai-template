import { useState } from 'react'
import { createFileRoute, useParams } from '@tanstack/react-router'
import { Plus, Inbox } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { IssueList } from '@/components/IssueList'
import { IssueListSkeleton } from '@/components/IssueListSkeleton'
import { CreateIssueDialog } from '@/components/CreateIssueDialog'
import { useTeams } from '@/hooks/useTeams'
import { useUser } from '@/hooks/useUser'
import { useIssues } from '@/hooks/useIssues'
import { useWorkflowStates } from '@/hooks/useWorkflowStates'
import { useLabels } from '@/hooks/useLabels'

/**
 * Issues view — the team-scoped grouped issues list.
 *
 * Groups issues by workflow status in canonical order (by WorkflowState
 * position) with accurate per-group counts; provides the create-issue dialog
 * (validated, optimistic insert + rollback). Polls on a short interval so the
 * list stays fresh (VAL-ISSUES-015–018, VAL-ISSUES-041, VAL-ISSUES-045,
 * VAL-ISSUES-047, VAL-ISSUES-049).
 */
export const Route = createFileRoute('/_authed/$team/issues')({
  component: IssuesView,
})

function IssuesView() {
  const { team: teamKey } = useParams({ strict: false })
  const [createOpen, setCreateOpen] = useState(false)

  const { data: teamsData, isLoading: teamsLoading } = useTeams()
  const { data: user } = useUser()

  const teamObj = (teamsData?.items ?? []).find((t) => t.key === teamKey)
  const teamId = teamObj?.id

  const issuesQuery = useIssues(teamId)
  const statesQuery = useWorkflowStates(teamId)
  const labelsQuery = useLabels(teamId)

  const workflowStates = statesQuery.data?.items ?? []
  const labels = labelsQuery.data?.items ?? []
  const issues = issuesQuery.data?.items ?? []

  // Resolve team members for the assignee picker (currently only the signed-in
  // user is known; expands when a members endpoint lands).
  const members = user
    ? [{ id: user.id, name: user.display_name || user.email }]
    : []
  const assigneeNames: Record<string, string> = Object.fromEntries(
    members.map((m) => [m.id, m.name]),
  )

  const initialLoading =
    teamsLoading ||
    (teamId ? issuesQuery.isLoading || statesQuery.isLoading : true)

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-6 py-3">
        <h1 className="text-base font-semibold text-foreground">Issues</h1>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4" />
          New issue
        </Button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-auto p-6">
        {initialLoading ? (
          <IssueListSkeleton groups={Math.min(workflowStates.length || 3, 5)} />
        ) : issuesQuery.isError ? (
          <ErrorState
            error={issuesQuery.error}
            onRetry={() => issuesQuery.refetch()}
            title="Couldn't load issues"
          />
        ) : issues.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title="No issues yet"
            description="Create your first issue to start tracking work in this team."
            action={
              <Button size="sm" onClick={() => setCreateOpen(true)}>
                <Plus className="h-4 w-4" />
                Create issue
              </Button>
            }
          />
        ) : (
          <IssueList
            issues={issues}
            workflowStates={workflowStates}
            assigneeNames={assigneeNames}
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
    </div>
  )
}
