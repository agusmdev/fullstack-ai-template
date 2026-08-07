import type { Label } from './label'

/** Lightweight label info embedded in issue responses (IssueLabelBrief). */
export interface IssueLabel {
  id: string
  name: string
  color: string | null
}

/**
 * Issue priority rank (mirrors the backend int 0–4).
 * 0 = Urgent … 4 = No priority (the default).
 */
export const PRIORITY_NONE = 4 as const

export interface PriorityLevel {
  value: number
  label: string
}

/** Canonical priority set, ordered Urgent → No priority. */
export const PRIORITIES: readonly PriorityLevel[] = [
  { value: 0, label: 'Urgent' },
  { value: 1, label: 'High' },
  { value: 2, label: 'Medium' },
  { value: 3, label: 'Low' },
  { value: 4, label: 'No priority' },
] as const

/** Shape of the backend `IssueResponse`. */
export interface Issue {
  id: string
  team_id: string
  identifier: string
  title: string
  description: string | null
  status_id: string
  priority: number
  assignee_id: string | null
  creator_id: string
  project_id: string | null
  cycle_id: string | null
  parent_id: string | null
  sort_order: number
  estimate: number | null
  due_date: string | null
  labels: IssueLabel[]
  created_at: string
  updated_at: string
}

/** Shape of a paginated `Page<IssueResponse>` from fastapi_pagination. */
export interface IssuesResponse {
  items: Issue[]
  total: number
  page: number
  size: number
  pages: number
}

/**
 * Sentinel value for the "Unassigned" assignee filter.
 *
 * The backend has no assignee UUID for unassigned issues, so the client sends
 * `unassigned=true` instead of `assignee_id=` when this sentinel is selected
 * (VAL-ISSUES-021).
 */
export const ASSIGNEE_UNASSIGNED = 'unassigned' as const

/** A single sort preset (label + backend ``order_by`` fields). */
export interface IssueSortPreset {
  key: string
  label: string
  /** Backend sort fields; prefix ``-`` for descending (e.g. ``-created_at``). */
  order_by: readonly string[]
}

/**
 * Canonical sort presets.
 *
 * - ``newest`` / ``oldest`` — sort by ``created_at`` (default is newest-first;
 *   VAL-ISSUES-026).
 * - ``updated`` — sort by ``updated_at`` desc (an edit reorders to the top;
 *   VAL-ISSUES-027).
 * - ``priority`` — sort by priority rank ascending (Urgent=0 first), with
 *   ``-created_at`` as a deterministic tiebreaker (VAL-ISSUES-028).
 */
export const SORT_PRESETS: readonly IssueSortPreset[] = [
  { key: 'newest', label: 'Newest first', order_by: ['-created_at'] },
  { key: 'oldest', label: 'Oldest first', order_by: ['created_at'] },
  { key: 'updated', label: 'Recently updated', order_by: ['-updated_at'] },
  { key: 'priority', label: 'Priority', order_by: ['priority', '-created_at'] },
] as const

/** Default sort key (newest-first by created date — VAL-ISSUES-026). */
export const DEFAULT_SORT_KEY = 'newest' as const

/** Resolve a sort key to its ``order_by`` fields (falls back to newest-first). */
export function sortKeyToOrderBy(sortKey: string | undefined): readonly string[] {
  return SORT_PRESETS.find((s) => s.key === sortKey)?.order_by ?? ['-created_at']
}

/** Resolve a sort key to its human label. */
export function sortKeyToLabel(sortKey: string | undefined): string {
  return SORT_PRESETS.find((s) => s.key === sortKey)?.label ?? 'Newest first'
}

/**
 * Filter/search/sort parameters for the issues list query. All optional — when
 * absent, the backend applies its defaults (no filter, newest-first). These are
 * applied **server-side** so the list matches the backend total exactly and
 * scales to long lists (VAL-ISSUES-019–028, VAL-ISSUES-029).
 *
 * ``assignee`` is a user UUID, the {@link ASSIGNEE_UNASSIGNED} sentinel, or
 * ``null`` (no filter).
 */
export interface IssuesQueryParams {
  search?: string
  status_id?: string | null
  priority?: number | null
  assignee?: string | null
  label_id?: string | null
  project_id?: string | null
  cycle_id?: string | null
  /** Sort preset key (see {@link SORT_PRESETS}); defaults to newest-first. */
  sort?: string
}

/** True when any filter/search/sort deviates from the default view. */
export function hasActiveIssueFilters(params: IssuesQueryParams): boolean {
  return Boolean(
    params.search?.trim() ||
      params.status_id ||
      params.priority != null ||
      params.assignee ||
      params.label_id ||
      params.project_id ||
      params.cycle_id ||
      (params.sort && params.sort !== DEFAULT_SORT_KEY),
  )
}

/**
 * Serialize filter/search/sort params into a stable, deterministic string for
 * use as a React Query key segment (so identical params produce the same key).
 */
export function serializeIssueParams(params: IssuesQueryParams): string {
  const parts = [
    params.search?.trim() ? `q:${params.search.trim()}` : '',
    params.status_id ? `s:${params.status_id}` : '',
    params.priority != null ? `p:${params.priority}` : '',
    params.assignee ? `a:${params.assignee}` : '',
    params.label_id ? `l:${params.label_id}` : '',
    params.project_id ? `pj:${params.project_id}` : '',
    params.cycle_id ? `cy:${params.cycle_id}` : '',
    params.sort && params.sort !== DEFAULT_SORT_KEY ? `o:${params.sort}` : '',
  ].filter(Boolean)
  return parts.join('|')
}

/**
 * Payload sent to `POST /issues`.
 *
 * `optimisticLabels` is never sent to the API — it carries resolved label
 * objects so the optimistically-inserted row can render label badges instantly
 * before the POST settles (the real issue refetch reconciles them afterwards).
 */
export interface CreateIssueInput {
  team_id: string
  title: string
  description?: string | null
  status_id: string | null
  priority: number
  assignee_id?: string | null
  label_ids?: string[]
  /** Parent issue id to create this issue as a sub-issue (VAL-SUBISSUES-001). */
  parent_id?: string | null
  /** Optimistic-only: resolved labels for instant display. Not serialized. */
  optimisticLabels?: Label[]
}

/**
 * Partial patch for `PATCH /issues/:id`. Only provided fields are sent; the
 * backend `IssueUpdate` is `@partial_model`. `id` + `team_id` target the issue
 * and scope the optimistic cache updates (VAL-ISSUES-031–036).
 */
export interface UpdateIssueInput {
  id: string
  team_id: string
  title?: string
  description?: string | null
  status_id?: string | null
  priority?: number
  assignee_id?: string | null
  project_id?: string | null
  cycle_id?: string | null
  /** Parent issue id (set to attach as sub-issue; null to detach). */
  parent_id?: string | null
}

/**
 * Add/remove a single label on an issue via the labels sub-resource
 * (`POST/DELETE /issues/:id/labels/:label_id`). `label` carries the resolved
 * label object so the optimistic update can render the badge instantly
 * (VAL-ISSUES-036).
 */
export interface IssueLabelToggleInput {
  id: string
  team_id: string
  label: IssueLabel
}
