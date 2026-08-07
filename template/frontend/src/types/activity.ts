/** Lightweight actor info embedded in an activity response (ActorBrief). */
export interface ActorBrief {
  id: string
  display_name: string
  email: string
}

/**
 * The activity kinds recorded by the backend. Mirror of the backend
 * ``app.modules.activity.models`` constants. Used to render a human-readable
 * description per entry.
 */
export const ACTIVITY_TYPES = {
  STATUS_CHANGE: 'status_change',
  ASSIGNEE_CHANGE: 'assignee_change',
  PRIORITY_CHANGE: 'priority_change',
  TITLE_RENAME: 'title_rename',
  LABEL_ADDED: 'label_added',
  LABEL_REMOVED: 'label_removed',
} as const

export type ActivityType = (typeof ACTIVITY_TYPES)[keyof typeof ACTIVITY_TYPES]

/** A {id, name} or {id, name, color} reference embedded in an activity payload. */
export interface ActivityRef {
  id: string
  name: string
  color?: string | null
}

/**
 * Structured detail for an activity entry. The shape depends on ``type``:
 *  - status_change:    { from: ActivityRef|null, to: ActivityRef|null }
 *  - assignee_change:  { from: ActivityRef|null, to: ActivityRef|null }
 *  - priority_change:  { from: number, to: number }
 *  - title_rename:     { from: string, to: string }
 *  - label_added:      { label: ActivityRef }
 *  - label_removed:    { label: ActivityRef }
 */
export interface ActivityPayload {
  from?: ActivityRef | number | string | null
  to?: ActivityRef | number | string | null
  label?: ActivityRef
  [key: string]: unknown
}

/**
 * An auto-generated, read-only activity entry for an issue.
 *
 * Entries are created by the backend on issue mutations; the feed is read-only
 * — there is no composer (VAL-ACTIVITY-009). The actor is eager-loaded so the
 * feed can render who performed the action (VAL-ACTIVITY-007).
 */
export interface Activity {
  id: string
  issue_id: string
  actor_id: string
  type: ActivityType
  payload: ActivityPayload
  actor: ActorBrief
  created_at: string
}

/** Shape of a paginated `Page<ActivityResponse>` from fastapi_pagination. */
export interface ActivityResponse {
  items: Activity[]
  total: number
  page: number
  size: number
  pages: number
}
