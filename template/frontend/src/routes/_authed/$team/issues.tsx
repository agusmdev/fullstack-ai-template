import { useMemo, useState } from 'react'
import { createFileRoute, useParams } from '@tanstack/react-router'
import { Plus, Inbox, SearchX, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { IssueList } from '@/components/IssueList'
import { IssueListSkeleton } from '@/components/IssueListSkeleton'
import { IssueFiltersBar } from '@/components/IssueFiltersBar'
import { CreateIssueDialog } from '@/components/CreateIssueDialog'
import { IssueDetailDrawer } from '@/components/IssueDetailDrawer'
import { useTeams } from '@/hooks/useTeams'
import { useUser } from '@/hooks/useUser'
import { useTeamRole } from '@/hooks/useTeamRole'
import { useIssues, flattenIssues, issuesTotal } from '@/hooks/useIssues'
import { useWorkflowStates } from '@/hooks/useWorkflowStates'
import { useLabels } from '@/hooks/useLabels'
import { useProjects } from '@/hooks/useProjects'
import { useDebounce } from '@/hooks/useDebounce'
import {
  DEFAULT_SORT_KEY,
  hasActiveIssueFilters,
  type Issue,
  type IssuesQueryParams,
} from '@/types/issue'

/** Debounce delay (ms) for the title search input. */
const SEARCH_DEBOUNCE_MS = 250

/**
 * Issues view — the team-scoped grouped issues list with server-side
 * filter/search/sort and "load more" pagination.
 *
 * - Groups issues by workflow status in canonical order (by WorkflowState
 *   position) with accurate per-group counts (VAL-ISSUES-015–018).
 * - Filter bar: status / priority / assignee (incl. Unassigned) / label, all
 *   applied server-side and composed with AND semantics (VAL-ISSUES-019–024).
 * - Title search is a case-insensitive substring, debounced (VAL-ISSUES-025).
 * - Sort by created (default newest-first) / updated / priority (VAL-ISSUES-026–028).
 * - Long lists paginate via "load more"; total matches the backend total
 *   (VAL-ISSUES-029). A distinct empty state shows when filters/search match
 *   nothing (VAL-ISSUES-046) vs. when the team has no issues (VAL-ISSUES-045).
 * - Polls on a short interval so the list stays fresh (VAL-ISSUES-049).
 */
export const Route = createFileRoute('/_authed/$team/issues')({
  component: IssuesView,
})

function IssuesView() {
  const { team: teamKey } = useParams({ strict: false })
  const [createOpen, setCreateOpen] = useState(false)
  // The currently-selected issue (for the detail drawer). Holds the issue object
  // already in the list cache so the drawer renders instantly without a flash,
  // while still refetching for freshness (VAL-ISSUES-030, VAL-ISSUES-048).
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null)

  // Filter/search/sort state. The search input is immediate (responsive UI);
  // a debounced copy feeds the query so typing doesn't fire a request per key.
  const [searchInput, setSearchInput] = useState('')
  const debouncedSearch = useDebounce(searchInput, SEARCH_DEBOUNCE_MS)
  const [params, setParams] = useState<IssuesQueryParams>({ sort: DEFAULT_SORT_KEY })

  // Effective params object passed to the query (stable per debounced value).
  const queryParams: IssuesQueryParams = useMemo(
    () => ({ ...params, search: debouncedSearch }),
    [params, debouncedSearch],
  )

  const { data: teamsData, isLoading: teamsLoading } = useTeams()
  const { data: user } = useUser()
  const { canWrite } = useTeamRole(teamKey)

  const teamObj = (teamsData?.items ?? []).find((t) => t.key === teamKey)
  const teamId = teamObj?.id

  const issuesQuery = useIssues(teamId, queryParams)
  const statesQuery = useWorkflowStates(teamId)
  const labelsQuery = useLabels(teamId)
  const projectsQuery = useProjects(teamId)

  const workflowStates = statesQuery.data?.items ?? []
  const labels = labelsQuery.data?.items ?? []
  const projects = projectsQuery.data?.items ?? []
  const issues = flattenIssues(issuesQuery.data)
  const total = issuesTotal(issuesQuery.data)
  const hasMore = issuesQuery.hasNextPage
  const fetchingMore = issuesQuery.isFetchingNextPage

  // Resolve team members for the assignee picker/filter (currently only the
  // signed-in user is known; expands when a members endpoint lands).
  const members = user
    ? [{ id: user.id, name: user.display_name || user.email }]
    : []
  const assigneeNames: Record<string, string> = Object.fromEntries(
    members.map((m) => [m.id, m.name]),
  )
  const projectNames: Record<string, string> = Object.fromEntries(
    projects.map((p) => [p.id, p.name]),
  )

  const hasActive = hasActiveIssueFilters(queryParams)
  const handleParamsChange = (patch: Partial<IssuesQueryParams>) =>
    setParams((prev) => ({ ...prev, ...patch }))
  const handleClear = () => {
    setParams({ sort: DEFAULT_SORT_KEY })
    setSearchInput('')
  }

  const initialLoading =
    teamsLoading || (teamId ? issuesQuery.isLoading || statesQuery.isLoading : true)

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-6 py-3">
        <h1 className="text-base font-semibold text-foreground">Issues</h1>
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

      {/* Filter bar (shown once data is available and there is something to
          filter, or an active filter to clear). */}
      {!initialLoading && (total > 0 || hasActive) && (
        <div className="border-b border-border px-6 py-2.5">
          <IssueFiltersBar
            params={queryParams}
            searchInput={searchInput}
            onSearchInputChange={setSearchInput}
            onParamsChange={handleParamsChange}
            onClear={handleClear}
            hasActive={hasActive}
            workflowStates={workflowStates}
            labels={labels}
            members={members}
          />
        </div>
      )}

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
        ) : total === 0 ? (
          hasActive ? (
            // Filters/search matched nothing (VAL-ISSUES-046).
            <EmptyState
              icon={SearchX}
              title="No matching issues"
              description="No issues match the current filters. Try adjusting or clearing them."
              action={
                <Button size="sm" variant="outline" onClick={handleClear}>
                  Clear filters
                </Button>
              }
            />
          ) : (
            // Team has no issues at all (VAL-ISSUES-045).
            <EmptyState
              icon={Inbox}
              title="No issues yet"
              description="Create your first issue to start tracking work in this team."
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
          <div className="flex flex-col gap-4">
            <IssueList
              issues={issues}
              workflowStates={workflowStates}
              assigneeNames={assigneeNames}
              projectNames={projectNames}
              onSelectIssue={setSelectedIssue}
            />

            {/* Pagination: load more for long lists (VAL-ISSUES-029). */}
            {hasMore && (
              <div className="flex items-center justify-center py-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => issuesQuery.fetchNextPage()}
                  disabled={fetchingMore}
                >
                  {fetchingMore ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading…
                    </>
                  ) : (
                    `Load more (${total - issues.length} remaining)`
                  )}
                </Button>
              </div>
            )}

            {/* Total count always reflects the backend total (VAL-ISSUES-029). */}
            {!hasMore && total > 0 && (
              <p className="py-1 text-center text-xs text-muted-foreground">
                {issues.length} of {total} issue{total === 1 ? '' : 's'}
              </p>
            )}
          </div>
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

      {/* Detail drawer (opens on row click). Closes by clearing the selection. */}
      <IssueDetailDrawer
        open={!!selectedIssue}
        onOpenChange={(o) => !o && setSelectedIssue(null)}
        issueId={selectedIssue?.id ?? null}
        initialIssue={selectedIssue ?? undefined}
        teamId={teamId ?? ''}
        workflowStates={workflowStates}
        labels={labels}
        projects={projects}
        members={members}
      />
    </div>
  )
}
