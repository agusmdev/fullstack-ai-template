import { UserRound } from 'lucide-react'
import { PriorityIcon } from '@/components/PriorityIcon'
import { StatusDot } from '@/components/StatusDot'
import { cn } from '@/lib/utils'
import { isOptimisticIssue } from '@/hooks/useIssues'
import type { Issue } from '@/types/issue'

interface IssueCardProps {
  issue: Issue
  /** Display name of the assignee, if any (resolved by the caller). */
  assigneeName?: string
  /** True when the issue is in a terminal status (completed/canceled). */
  isTerminal?: boolean
  /** Called when the card is clicked (not dragged) to open the detail drawer. */
  onSelect?: (issue: Issue) => void
  /** Called when a drag starts on this card (carries the issue id). */
  onDragStart?: (issue: Issue) => void
  /** Called when a drag ends on this card (cleanup signal). */
  onDragEnd?: () => void
  /** Disable DnD (e.g. for optimistic/pending rows). */
  draggable?: boolean
  className?: string
}

/**
 * A single kanban card on the board. Shows the auto-identifier (`TEAM-NN`),
 * title, priority glyph, label badges, and assignee avatar
 * (VAL-BOARD-002).
 *
 * The card is **draggable** via native HTML5 DnD (the `draggable` attribute +
 * `onDragStart`/`onDragEnd`). Dragging between columns triggers a status change
 * (VAL-BOARD-003). The non-DnD move path is the card's status picker on the
 * board route (VAL-BOARD-004).
 *
 * Clicking the card (without dragging) opens the detail drawer. Optimistic rows
 * render dimmed and are not draggable.
 * Terminal-status cards (completed/canceled) render muted with a strikethrough
 * title (VAL-ISSUES-044).
 */
export function IssueCard({
  issue,
  assigneeName,
  isTerminal,
  onSelect,
  onDragStart,
  onDragEnd,
  draggable = true,
  className,
}: IssueCardProps) {
  const optimistic = isOptimisticIssue(issue)
  const canDrag = draggable && !optimistic
  const interactive = !!onSelect
  const initials =
    assigneeName
      ?.split(/\s+/)
      .map((p) => p[0])
      .filter(Boolean)
      .slice(0, 2)
      .join('')
      .toUpperCase() ?? ''

  return (
    <div
      role={interactive ? 'button' : undefined}
      tabIndex={interactive ? 0 : undefined}
      draggable={canDrag}
      onDragStart={(e) => {
        if (!canDrag) {
          e.preventDefault()
          return
        }
        // Carry the issue id so the drop target knows what to move.
        e.dataTransfer.setData('text/plain', issue.id)
        e.dataTransfer.effectAllowed = 'move'
        onDragStart?.(issue)
      }}
      onDragEnd={() => onDragEnd?.()}
      onClick={interactive ? () => onSelect?.(issue) : undefined}
      onKeyDown={
        interactive
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                onSelect?.(issue)
              }
            }
          : undefined
      }
      aria-label={`${issue.identifier || 'issue'}: ${issue.title}`}
      className={cn(
        'group flex cursor-grab flex-col gap-1.5 rounded-lg border border-border bg-card p-3 shadow-sm transition-colors active:cursor-grabbing',
        interactive && 'hover:border-primary/40 hover:shadow-md focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-hidden',
        optimistic && 'cursor-default opacity-60',
        isTerminal && 'opacity-70',
        className,
      )}
    >
      {/* Labels row (badges) */}
      {issue.labels.length > 0 && (
        <div className="flex flex-wrap items-center gap-1">
          {issue.labels.map((label) => (
            <span
              key={label.id}
              className="inline-flex items-center gap-1 rounded-full border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground"
            >
              <StatusDot color={label.color} className="h-2 w-2 shrink-0" />
              <span className="max-w-[6rem] truncate">{label.name}</span>
            </span>
          ))}
        </div>
      )}

      {/* Title */}
      <p
        className={cn(
          'text-sm leading-snug text-foreground',
          isTerminal && 'text-muted-foreground line-through',
        )}
      >
        {issue.title}
      </p>

      {/* Footer: identifier + priority + assignee */}
      <div className="mt-0.5 flex items-center gap-2">
        <PriorityIcon priority={issue.priority} />
        <span className="font-mono text-[11px] text-muted-foreground">
          {issue.identifier || '···'}
        </span>
        <div className="ml-auto">
          {issue.assignee_id ? (
            <span
              className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/15 text-[9px] font-semibold text-primary"
              title={assigneeName ?? 'Assigned'}
            >
              {initials || '?'}
            </span>
          ) : (
            <span className="flex h-5 w-5 items-center justify-center rounded-full text-muted-foreground/40">
              <UserRound className="h-3 w-3" />
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
