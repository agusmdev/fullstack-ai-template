import { UserRound } from 'lucide-react'
import { PriorityIcon } from '@/components/PriorityIcon'
import { StatusDot } from '@/components/StatusDot'
import { cn } from '@/lib/utils'
import { isOptimisticIssue } from '@/hooks/useIssues'
import type { Issue } from '@/types/issue'

interface IssueRowProps {
  issue: Issue
  /** Display name of the assignee, if any (resolved by the caller). */
  assigneeName?: string
  className?: string
}

/**
 * A single issue row in the grouped list. Shows the auto-identifier
 * (`TEAM-NN`), title, priority glyph, label badges, and assignee avatar.
 *
 * Optimistically-inserted rows render a pending identifier placeholder until the
 * POST settles and the real issue reconciles (VAL-ISSUES-008, VAL-ISSUES-011).
 */
export function IssueRow({ issue, assigneeName, className }: IssueRowProps) {
  const optimistic = isOptimisticIssue(issue)
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
      className={cn(
        'group flex items-center gap-3 rounded-md border border-border bg-card px-3 py-2 transition-colors hover:bg-accent/50',
        optimistic && 'opacity-60',
        className,
      )}
    >
      <PriorityIcon priority={issue.priority} />

      <span className="w-16 shrink-0 font-mono text-xs text-muted-foreground">
        {issue.identifier || '···'}
      </span>

      <span className="min-w-0 flex-1 truncate text-sm text-foreground">
        {issue.title}
      </span>

      {issue.labels.length > 0 && (
        <div className="hidden items-center gap-1 sm:flex">
          {issue.labels.map((label) => (
            <span
              key={label.id}
              className="inline-flex items-center gap-1 rounded-full border border-border px-2 py-0.5 text-[11px] text-muted-foreground"
            >
              <StatusDot color={label.color} className="h-2 w-2" />
              {label.name}
            </span>
          ))}
        </div>
      )}

      {issue.assignee_id ? (
        <span
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/15 text-[10px] font-semibold text-primary"
          title={assigneeName ?? 'Assigned'}
        >
          {initials || '?'}
        </span>
      ) : (
        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-muted-foreground/40">
          <UserRound className="h-3.5 w-3.5" />
        </span>
      )}
    </div>
  )
}
