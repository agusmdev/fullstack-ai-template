import { DEFAULT_SORT_KEY, type IssuesQueryParams } from '@/types/issue'

/**
 * URL search-param shape shared by the Issues **list** and **Board** views.
 *
 * Storing filters in the URL lets the list↔board toggle carry the exact same
 * scope + filters (VAL-BOARD-005): switching views is just a route change that
 * preserves the query string, so the underlying issue set is identical.
 */
export interface IssueUrlSearch {
  /** Title search query (debounced by the caller before committing to URL). */
  q?: string
  status_id?: string
  priority?: number
  /** Assignee UUID or the `'unassigned'` sentinel. */
  assignee?: string
  label_id?: string
  /** Sort preset key; defaults to {@link DEFAULT_SORT_KEY}. */
  sort?: string
}

/**
 * TanStack Router `validateSearch` parser — coerces raw URL search params into
 * the typed {@link IssueUrlSearch} shape, dropping empty/junk values and
 * defaulting `sort`.
 *
 * Used by both `/$team/issues` and `/$team/board` so they accept the same URL
 * params and the toggle preserves filters bidirectionally.
 */
export function validateIssueSearch(input: Record<string, unknown>): IssueUrlSearch {
  const result: IssueUrlSearch = {}

  const q = typeof input.q === 'string' ? input.q.trim() : ''
  if (q) result.q = q

  const statusId = typeof input.status_id === 'string' ? input.status_id.trim() : ''
  if (statusId) result.status_id = statusId

  if (input.priority != null && input.priority !== '') {
    const p = Number(input.priority)
    if (Number.isInteger(p)) result.priority = p
  }

  const assignee = typeof input.assignee === 'string' ? input.assignee.trim() : ''
  if (assignee) result.assignee = assignee

  const labelId = typeof input.label_id === 'string' ? input.label_id.trim() : ''
  if (labelId) result.label_id = labelId

  const sort = typeof input.sort === 'string' ? input.sort.trim() : ''
  result.sort = sort || DEFAULT_SORT_KEY

  return result
}

/**
 * Convert the validated URL search into the {@link IssuesQueryParams} consumed
 * by `useIssues`.
 */
export function urlSearchToParams(search: IssueUrlSearch): IssuesQueryParams {
  return {
    search: search.q,
    status_id: search.status_id ?? null,
    priority: search.priority ?? null,
    assignee: search.assignee ?? null,
    label_id: search.label_id ?? null,
    sort: search.sort ?? DEFAULT_SORT_KEY,
  }
}

/**
 * Build the default (cleared) URL search object — only the default sort is kept.
 * Used by the "Clear" action.
 */
export function defaultIssueSearch(): IssueUrlSearch {
  return { sort: DEFAULT_SORT_KEY }
}
