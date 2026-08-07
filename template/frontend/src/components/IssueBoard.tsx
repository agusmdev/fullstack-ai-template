import { useMemo, useState } from 'react'
import { IssueCard } from '@/components/IssueCard'
import { StatusDot } from '@/components/StatusDot'
import { groupIssuesByStatus } from '@/components/IssueList'
import { cn } from '@/lib/utils'
import type { Issue } from '@/types/issue'
import type { WorkflowState } from '@/types/workflow-state'

interface IssueBoardProps {
  issues: Issue[]
  workflowStates: WorkflowState[]
  /** Optional lookup of assignee id → display name (for card avatars). */
  assigneeNames?: Record<string, string>
  /** Called when a card is dragged or clicked to open the detail drawer. */
  onSelectIssue?: (issue: Issue) => void
  /**
   * Called when a card is dropped onto a column (status change via DnD).
   * Receives the issue id and the target status (WorkflowState) id.
   */
  onMoveIssue?: (issueId: string, targetStatusId: string) => void
  /** Disable interactions (e.g. while data is loading). */
  disabled?: boolean
}

/**
 * The kanban board — one column per workflow status, ordered by `position`
 * (VAL-BOARD-001).
 *
 * Each column is a **drop target**: dragging a card over it highlights the
 * column, and dropping calls {@link onMoveIssue} to change the issue's status
 * (VAL-BOARD-003). Empty columns render a drop-hint placeholder and remain valid
 * drop targets (VAL-BOARD-007).
 *
 * Cards show key metadata (identifier, title, priority, assignee, labels) via
 * {@link IssueCard} (VAL-BOARD-002). The optimistic move + rollback is handled
 * by the `useUpdateIssue` hook on the route — this component only signals the
 * intent.
 */
export function IssueBoard({
  issues,
  workflowStates,
  assigneeNames,
  onSelectIssue,
  onMoveIssue,
  disabled,
}: IssueBoardProps) {
  const groups = useMemo(
    () => groupIssuesByStatus(issues, workflowStates),
    [issues, workflowStates],
  )

  // Track which column the dragged card is currently over (for highlight).
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null)
  // Track whether a drag is in flight (to show drop hints on empty columns).
  const [isDragging, setIsDragging] = useState(false)

  const handleDrop = (targetStatusId: string, dataTransfer: DataTransfer) => {
    const issueId = dataTransfer.getData('text/plain')
    setDragOverColumn(null)
    setIsDragging(false)
    if (issueId && onMoveIssue) {
      onMoveIssue(issueId, targetStatusId)
    }
  }

  return (
    <div
      className="flex h-full gap-3 overflow-x-auto pb-2"
      onDragEnd={() => {
        // Safety cleanup if a drag ends without a drop (e.g. dropped outside).
        setDragOverColumn(null)
        setIsDragging(false)
      }}
    >
      {groups.map(({ state, issues: groupIssues }) => {
        const isOver = dragOverColumn === state.id
        const stateType = state.type
        return (
          <section
            key={state.id}
            aria-label={`${state.name} column`}
            className="flex w-72 shrink-0 flex-col rounded-lg bg-muted/40"
            onDragOver={(e) => {
              if (disabled) return
              e.preventDefault() // required to allow drop
              e.dataTransfer.dropEffect = 'move'
              if (dragOverColumn !== state.id) setDragOverColumn(state.id)
            }}
            onDragEnter={(e) => {
              if (disabled) return
              e.preventDefault()
              if (dragOverColumn !== state.id) setDragOverColumn(state.id)
            }}
            onDragLeave={(e) => {
              // Only clear if the pointer truly left this column (not entering
              // a child). relatedTarget is null when leaving the viewport.
              if (!e.currentTarget.contains(e.relatedTarget as Node | null)) {
                setDragOverColumn((prev) => (prev === state.id ? null : prev))
              }
            }}
            onDrop={(e) => {
              e.preventDefault()
              handleDrop(state.id, e.dataTransfer)
            }}
          >
            {/* Column header */}
            <div className="flex items-center gap-2 px-3 py-2.5">
              <StatusDot color={state.color} type={stateType} />
              <h3 className="text-sm font-medium text-foreground">{state.name}</h3>
              <span className="text-xs text-muted-foreground">{groupIssues.length}</span>
            </div>

            {/* Card list (drop zone) */}
            <div
              className={cn(
                'flex flex-1 flex-col gap-2 overflow-y-auto px-2 pb-2 transition-colors',
                isOver && 'bg-primary/5',
              )}
            >
              {groupIssues.length === 0 ? (
                <div
                  className={cn(
                    'flex min-h-[4rem] items-center justify-center rounded-md border border-dashed text-xs text-muted-foreground/50 transition-colors',
                    isOver && 'border-primary/40 bg-primary/5 text-primary/70',
                  )}
                >
                  {isDragging ? 'Drop here' : 'No issues'}
                </div>
              ) : (
                groupIssues.map((issue) => (
                  <IssueCard
                    key={issue.id}
                    issue={issue}
                    assigneeName={
                      issue.assignee_id ? assigneeNames?.[issue.assignee_id] : undefined
                    }
                    isTerminal={stateType === 'completed' || stateType === 'canceled'}
                    onSelect={onSelectIssue}
                    onDragStart={() => setIsDragging(true)}
                    onDragEnd={() => {
                      setIsDragging(false)
                      setDragOverColumn(null)
                    }}
                    draggable={!disabled}
                  />
                ))
              )}
            </div>
          </section>
        )
      })}
    </div>
  )
}
