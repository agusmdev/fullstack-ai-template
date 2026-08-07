import { useMemo, useState } from 'react'
import { ChevronRight, ChevronDown } from 'lucide-react'
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
 *
 * **All** issues are grouped (including sub-issues) so the **board** shows each
 * sub-issue card in its own-status column (VAL-SUBISSUES-004). The ``IssueList``
 * component separately filters out children (issues with ``parent_id``) before
 * grouping so they render nested under their parent instead (VAL-SUBISSUES-002).
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
  /** Optional lookup of project_id → project name (for row project badges). */
  projectNames?: Record<string, string>
  /** Called when a row is activated to open the detail drawer. */
  onSelectIssue?: (issue: Issue) => void
}

/**
 * The grouped issues list. Each group renders a header (status dot + name +
 * accurate count) followed by its rows.
 *
 * Sub-issues (children with ``parent_id`` set) render **nested/indented** under
 * their parent in the list, with an expand/collapse toggle and a child count
 * (VAL-SUBISSUES-002). Children are NOT grouped by their own status in the list
 * — they appear under the parent regardless of status. (On the board, children
 * appear under their own status column — VAL-SUBISSUES-004.)
 */
export function IssueList({ issues, workflowStates, assigneeNames, projectNames, onSelectIssue }: IssueListProps) {
  // Separate top-level issues from children (sub-issues). Only top-level
  // issues are grouped by status; children are nested under their parent
  // (VAL-SUBISSUES-002).
  const topLevelIssues = useMemo(
    () => issues.filter((i) => !i.parent_id),
    [issues],
  )

  const groups = useMemo(
    () => groupIssuesByStatus(topLevelIssues, workflowStates),
    [topLevelIssues, workflowStates],
  )

  // Build a lookup of parentId → children for nesting.
  const childrenByParent = useMemo(() => {
    const m = new Map<string, Issue[]>()
    for (const issue of issues) {
      if (!issue.parent_id) continue
      const arr = m.get(issue.parent_id) ?? []
      arr.push(issue)
      m.set(issue.parent_id, arr)
    }
    return m
  }, [issues])

  // Collapse state: a Set of **collapsed** parent issue IDs. All parents are
  // expanded by default; only those the user has collapsed are hidden. This
  // ensures parents with children added after mount (e.g. via the drawer) are
  // automatically expanded (VAL-SUBISSUES-002).
  const [collapsed, setCollapsed] = useState<Set<string>>(() => new Set())

  const toggleExpand = (id: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  // Lookup of status_id → workflow state type, to mark terminal rows.
  const stateTypeById = useMemo(() => {
    const m = new Map<string, string>()
    for (const s of workflowStates) m.set(s.id, s.type)
    return m
  }, [workflowStates])

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
              groupIssues.map((issue) => {
                const type = stateTypeById.get(issue.status_id)
                const children = childrenByParent.get(issue.id) ?? []
                const isExpanded = !collapsed.has(issue.id)
                const hasChildren = children.length > 0
                return (
                  <div key={issue.id} className="flex flex-col gap-1">
                    <div className="flex items-center gap-1">
                      {/* Expand/collapse toggle for parents with children */}
                      {hasChildren ? (
                        <button
                          type="button"
                          className="flex h-7 w-5 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-accent"
                          onClick={() => toggleExpand(issue.id)}
                          aria-label={isExpanded ? 'Collapse sub-issues' : 'Expand sub-issues'}
                        >
                          {isExpanded ? (
                            <ChevronDown className="h-3.5 w-3.5" />
                          ) : (
                            <ChevronRight className="h-3.5 w-3.5" />
                          )}
                        </button>
                      ) : (
                        <span className="w-5 shrink-0" />
                      )}
                      <div className="min-w-0 flex-1">
                        <IssueRow
                          issue={issue}
                          assigneeName={issue.assignee_id ? assigneeNames?.[issue.assignee_id] : undefined}
                          projectName={issue.project_id ? projectNames?.[issue.project_id] : undefined}
                          isTerminal={type === 'completed' || type === 'canceled'}
                          onSelect={onSelectIssue}
                        />
                      </div>
                      {/* Child count badge (VAL-SUBISSUES-002/006) */}
                      {hasChildren && (
                        <span className="shrink-0 rounded-full bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                          {children.length}
                        </span>
                      )}
                    </div>
                    {/* Nested children (indented) — VAL-SUBISSUES-002 */}
                    {hasChildren && isExpanded && (
                      <div className="flex flex-col gap-1">
                        {children.map((child) => {
                          const childType = stateTypeById.get(child.status_id)
                          return (
                            <IssueRow
                              key={child.id}
                              issue={child}
                              assigneeName={child.assignee_id ? assigneeNames?.[child.assignee_id] : undefined}
                              projectName={child.project_id ? projectNames?.[child.project_id] : undefined}
                              isTerminal={childType === 'completed' || childType === 'canceled'}
                              indent={1}
                              onSelect={onSelectIssue}
                            />
                          )
                        })}
                      </div>
                    )}
                  </div>
                )
              })
            )}
          </div>
        </section>
      ))}
    </div>
  )
}
