/** Shape of the backend `CycleResponse`. */
export interface Cycle {
  id: string
  team_id: string
  name: string
  /** ISO date string (start of the cycle window, inclusive). */
  starts_at: string
  /** ISO date string (end of the cycle window, inclusive; after starts_at). */
  ends_at: string
  /** ISO date string when the cycle was completed (null while active/upcoming). */
  completed_at: string | null
  created_at: string
  updated_at: string
}

/** Shape of a paginated `Page<CycleResponse>` from fastapi_pagination. */
export interface CyclesResponse {
  items: Cycle[]
  total: number
  page: number
  size: number
  pages: number
}

/** Temporal state of a cycle relative to "now". */
export type CyclePhase = 'past' | 'active' | 'upcoming'

/**
 * Determine a cycle's phase relative to today.
 *
 * - ``past``: ended before today (ends_at < today).
 * - ``active``: today falls within [starts_at, ends_at].
 * - ``upcoming``: starts after today (starts_at > today).
 *
 * VAL-CYCLES-008: past/active/upcoming distinguishable where exposed.
 */
export function cyclePhase(cycle: Pick<Cycle, 'starts_at' | 'ends_at'>): CyclePhase {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const start = new Date(cycle.starts_at)
  start.setHours(0, 0, 0, 0)
  const end = new Date(cycle.ends_at)
  end.setHours(0, 0, 0, 0)

  if (today < start) return 'upcoming'
  if (today > end) return 'past'
  return 'active'
}

/** Format an ISO date string into a short date (never Invalid Date). */
export function formatCycleDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

/**
 * Format the start→end window compactly (e.g. "Aug 1 – Aug 14, 2026").
 * VAL-CYCLES-008: date window surfaced formatted.
 */
export function formatCycleWindow(cycle: Pick<Cycle, 'starts_at' | 'ends_at'>): string {
  const start = new Date(cycle.starts_at)
  const end = new Date(cycle.ends_at)
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return '—'
  const sameYear = start.getFullYear() === end.getFullYear()
  const startStr = start.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    ...(sameYear ? {} : { year: 'numeric' }),
  })
  const endStr = end.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
  return `${startStr} – ${endStr}`
}

/**
 * Cycle progress derived from issues.
 *
 * "Done" = issues whose workflow status type is terminal (completed/canceled).
 * VAL-CYCLES-006: progress reflects issue completion.
 */
export interface CycleProgress {
  done: number
  total: number
}

/**
 * Compute cycle progress (X of Y done) from the cycle's issues and the team's
 * workflow states. An issue counts as done when its status type is
 * ``completed`` or ``canceled``.
 */
export function computeCycleProgress(
  issues: { status_id: string }[],
  workflowStateTypes: Map<string, string>,
): CycleProgress {
  let done = 0
  for (const issue of issues) {
    const type = workflowStateTypes.get(issue.status_id)
    if (type === 'completed' || type === 'canceled') done += 1
  }
  return { done, total: issues.length }
}
