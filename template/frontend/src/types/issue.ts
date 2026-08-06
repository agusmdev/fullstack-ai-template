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
  /** Optimistic-only: resolved labels for instant display. Not serialized. */
  optimisticLabels?: Label[]
}
