import { Activity as ActivityIcon, Loader2 } from 'lucide-react'
import { useActivity } from '@/hooks/useActivity'
import { ACTIVITY_TYPES, type Activity } from '@/types/activity'
import { priorityLabel } from '@/components/PriorityIcon'
import { formatRelativeTime } from '@/lib/format-time'

interface ActivityFeedProps {
  /** The issue whose activity feed to display. */
  issueId: string
  /** The issue's team id (scopes the read; unused for auth beyond enabling). */
  teamId: string
}

/** Resolve a {id,name} reference to its display name (or "Unassigned"/"—"). */
function refName(ref: unknown): string {
  if (ref && typeof ref === 'object' && 'name' in ref) {
    return String((ref as { name: string }).name)
  }
  return '—'
}

/**
 * Render a human-readable description for an activity entry's payload.
 *
 * Each kind produces a short phrase describing the mutation (from→to where
 * relevant). The actor name and timestamp are rendered separately so every
 * entry shows actor + type + time (VAL-ACTIVITY-007).
 */
function describeActivity(a: Activity): string {
  const p = a.payload
  switch (a.type) {
    case ACTIVITY_TYPES.STATUS_CHANGE:
      return `changed status from ${refName(p.from)} to ${refName(p.to)}`
    case ACTIVITY_TYPES.ASSIGNEE_CHANGE: {
      const from = refName(p.from)
      const to = refName(p.to)
      if (!p.to) return 'removed the assignee'
      if (!p.from || from === '—') return `assigned to ${to}`
      return `reassigned from ${from} to ${to}`
    }
    case ACTIVITY_TYPES.PRIORITY_CHANGE: {
      const from =
        typeof p.from === 'number' ? priorityLabel(p.from) : String(p.from ?? '—')
      const to =
        typeof p.to === 'number' ? priorityLabel(p.to) : String(p.to ?? '—')
      return `changed priority from ${from} to ${to}`
    }
    case ACTIVITY_TYPES.TITLE_RENAME:
      return `renamed the issue`
    case ACTIVITY_TYPES.LABEL_ADDED:
      return `added the ${refName(p.label)} label`
    case ACTIVITY_TYPES.LABEL_REMOVED:
      return `removed the ${refName(p.label)} label`
    default:
      return 'updated the issue'
  }
}

/**
 * Activity feed — a read-only audit trail shown in the issue detail drawer.
 *
 * - Lists auto-generated activity entries newest-first with the actor and a
 *   human-readable timestamp (VAL-ACTIVITY-001..007).
 * - Updates automatically within the polling window after a mutation — no
 *   manual reload (VAL-ACTIVITY-008).
 * - Explicit empty state when the issue has no activity.
 * - Read-only: there is no composer — clients cannot author free-text activity
 *   (VAL-ACTIVITY-009).
 */
export function ActivityFeed({ issueId, teamId }: ActivityFeedProps) {
  const activityQuery = useActivity(issueId, teamId)
  const entries = activityQuery.data?.items ?? []

  return (
    <div className="mt-6 border-t border-border pt-4" data-testid="activity-feed">
      <div className="mb-2 flex items-center gap-1.5">
        <ActivityIcon className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="text-xs font-medium text-muted-foreground">Activity</span>
        {entries.length > 0 && (
          <span className="text-xs text-muted-foreground/70">{entries.length}</span>
        )}
      </div>

      {activityQuery.isLoading ? (
        <div className="flex items-center gap-1.5 px-1 py-1 text-xs text-muted-foreground">
          <Loader2 className="h-3 w-3 animate-spin" />
          Loading…
        </div>
      ) : entries.length === 0 ? (
        <p className="px-1 py-1 text-xs text-muted-foreground/60" data-testid="activity-empty">
          No activity yet.
        </p>
      ) : (
        <div className="flex flex-col gap-2.5" data-testid="activity-list">
          {entries.map((entry) => (
            <ActivityItem key={entry.id} entry={entry} />
          ))}
        </div>
      )}
    </div>
  )
}

interface ActivityItemProps {
  entry: Activity
}

/** A single read-only activity row: actor avatar, description, and timestamp. */
function ActivityItem({ entry }: ActivityItemProps) {
  const name =
    entry.actor.display_name?.trim() || entry.actor.email || 'Unknown'
  return (
    <div className="flex gap-2.5" data-testid="activity-item">
      <Avatar name={name} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span
            className="truncate text-xs font-medium text-foreground"
            data-testid="activity-actor"
          >
            {name}
          </span>
          <span
            className="shrink-0 text-[11px] text-muted-foreground"
            data-testid="activity-time"
          >
            {formatRelativeTime(entry.created_at)}
          </span>
        </div>
        <p
          className="mt-0.5 text-xs text-muted-foreground"
          data-testid="activity-description"
        >
          {describeActivity(entry)}
        </p>
      </div>
    </div>
  )
}

/** A small initials avatar (no external dependency). */
function Avatar({ name }: { name: string }) {
  const initials = name
    .split(/\s+/)
    .map((part) => part[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()
  return (
    <div
      className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-muted text-[10px] font-medium text-muted-foreground"
      aria-hidden="true"
    >
      {initials || '?'}
    </div>
  )
}
