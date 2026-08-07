/**
 * Shape of the backend `ViewResponse` — a saved issue view capturing filters +
 * group_by + order_by (VAL-VIEWS-001).
 *
 * ``filters`` is a JSONB snapshot of the active filter values
 * (``q``/``status_id``/``priority``/``assignee``/``label_id``); ``order_by`` is
 * the sort preset key; ``group_by`` is the grouping mode.
 */
export interface View {
  id: string
  owner_id: string | null
  team_id: string
  name: string
  filters: Record<string, unknown>
  group_by: string | null
  order_by: string | null
  description: string | null
  created_at: string
  updated_at: string
}

/** Shape of a paginated `Page<ViewResponse>` from fastapi_pagination. */
export interface ViewsResponse {
  items: View[]
  total: number
  page: number
  size: number
  pages: number
}
