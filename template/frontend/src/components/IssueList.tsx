import { useMemo } from 'react'
import { ChevronRight } from 'lucide-react'
import { IssueRow } from '@/components/IssueRow'
import { StatusDot } from '@/components/StatusDot'
import type { Issue } from '@/types/issue'
import type { WorkflowState } from '@/types/workflow-state'

/** A status group with its issues, in canonical workflow order. */
export interface IssueGroup {
  state: WorkflowState
  issues: Issue[]
}

/**
 * Partition issues into status groups ordered by WorkflowState `position`
 * (Backlog → Unstarted → Started → Completed → Canceled), so the list always
 * shows canonical grouping regardless of how issues are sorted (VAL-ISSUES-015,
 * VAL-ISSUES-016). Empty groups are included with count 0 (VAL-ISSUES-018).
 */
export function groupIssuesByStatus(
  issues: Issue[],
  workflowStates: WorkflowState[],
): IssueGroup[] {
  const byStatus = new Map<string, Issue[]>()
  for (const issue of issues) {
    const arr = byStatus.get(issue.status_id) ?? []
    arr.push(issue)
    byStatus.set(issue.status_id, arr)
  }
  return workflowStates.map((state) => ({
    state,
    issues: byStatus.get(state.id) ?? [],
  }))
}

interface IssueListProps {
  issues: Issue[]
  workflowStates: WorkflowState[]
  /** Optional lookup of assignee id → display name (for row avatars). */
  assigneeNames?: Record<string, string>
}

/**
 * The grouped issues list. Each group renders a header (status dot + name +
 * accurate count) followed by its rows. Used by the issues route.
 */
export function IssueList({ issues, workflowStates, assigneeNames }: IssueListProps) {
  const groups = useMemo(
    () => groupIssuesByStatus(issues, workflowStates),
    [issues, workflowStates],
  )

  return (
    <div className="flex flex-col gap-4">
      {groups.map(({ state, issues: groupIssues }) => (
        <section key={state.id} aria-label={`${state.name} issues`}>
          <div className="mb-1.5 flex items-center gap-2 px-1">
            <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
            <StatusDot color={state.color} type={state.type} />
            <h2 className="text-sm font-medium text-foreground">{state.name}</h2>
            <span className="text-xs text-muted-foreground">{groupIssues.length}</span>
          </div>
          <div className="flex flex-col gap-1">
            {groupIssues.length === 0 ? (
              <p className="px-3 py-2 text-xs text-muted-foreground/60">
                No issues
              </p>
            ) : (
              groupIssues.map((issue) => (
                <IssueRow
                  key={issue.id}
                  issue={issue}
                  assigneeName={issue.assignee_id ? assigneeNames?.[issue.assignee_id] : undefined}
                />
              ))
            )}
          </div>
        </section>
      ))}
    </div>
  )
}
