import {
  DEFAULT_SORT_KEY,
  type IssuesQueryParams,
} from '@/types/issue'
import type { IssueUrlSearch } from '@/lib/issue-search'
import type { View } from '@/types/view'

/**
 * The grouping mode currently surfaced by the Issues/Board views. Both views
 * always group by workflow status today, so a saved view's ``group_by`` is
 * ``'status'``. Stored on the View so future grouping modes round-trip without
 * a schema change (VAL-VIEWS-001).
 */
export const DEFAULT_GROUP_BY = 'status' as const

/**
 * The filter fields persisted in a View's ``filters`` JSONB. These mirror the
 * URL search-param names shared by the Issues list and Board
 * (see {@link IssueUrlSearch}) so a saved view can be applied by navigating to
 * the route with the stored search params.
 */
export interface ViewFilters {
  q?: string
  status_id?: string
  priority?: number
  assignee?: string
  label_id?: string
}

/**
 * Convert a saved View's stored configuration into the {@link IssueUrlSearch}
 * used to navigate to the Issues/Board route (apply the view — VAL-VIEWS-003).
 *
 * ``filters`` carries the filter values; ``order_by`` carries the sort preset
 * key (falling back to the default). ``group_by`` is not part of the URL today
 * (grouping is always by status) but is applied by the consuming view.
 */
export function viewToUrlSearch(view: View): IssueUrlSearch {
  const filters = (view.filters ?? {}) as ViewFilters
  const search: IssueUrlSearch = { sort: view.order_by || DEFAULT_SORT_KEY }
  if (filters.q) search.q = filters.q
  if (filters.status_id) search.status_id = filters.status_id
  if (filters.priority != null) search.priority = filters.priority
  if (filters.assignee) search.assignee = filters.assignee
  if (filters.label_id) search.label_id = filters.label_id
  return search
}

/**
 * Capture the current view configuration (filters + group_by + sort) from the
 * URL search, for saving as a View (VAL-VIEWS-001). Only non-default values are
 * stored so the saved snapshot is minimal and stable.
 */
export function urlSearchToViewConfig(
  search: IssueUrlSearch,
): { filters: ViewFilters; group_by: string; order_by: string } {
  const filters: ViewFilters = {}
  if (search.q) filters.q = search.q
  if (search.status_id) filters.status_id = search.status_id
  if (search.priority != null) filters.priority = search.priority
  if (search.assignee) filters.assignee = search.assignee
  if (search.label_id) filters.label_id = search.label_id
  return {
    filters,
    group_by: DEFAULT_GROUP_BY,
    order_by: search.sort || DEFAULT_SORT_KEY,
  }
}

/**
 * Canonical key for a search object — used to compare two configurations for
 * equality (active-view highlighting + dirty detection). Empty/undefined values
 * are dropped and the sort defaults, so ``{}`` and ``{ sort: 'newest' }`` are
 * considered identical.
 */
function searchSignature(search: IssueUrlSearch): string {
  const parts = [
    search.q?.trim() ? `q:${search.q.trim()}` : '',
    search.status_id ? `s:${search.status_id}` : '',
    search.priority != null ? `p:${search.priority}` : '',
    search.assignee ? `a:${search.assignee}` : '',
    search.label_id ? `l:${search.label_id}` : '',
    `o:${search.sort || DEFAULT_SORT_KEY}`,
  ].filter(Boolean)
  return parts.join('|')
}

/**
 * Does the current URL search match a saved view's stored configuration?
 *
 * Used for active-view highlighting (VAL-VIEWS-003) and dirty detection
 * (VAL-VIEWS-006): after applying a saved view the signatures match (active);
 * after the user changes a filter the signatures diverge (no longer active),
 * but the stored view is never overwritten unless explicitly re-saved.
 */
export function viewMatchesSearch(view: View, search: IssueUrlSearch): boolean {
  return searchSignature(viewToUrlSearch(view)) === searchSignature(search)
}

/**
 * Whether the current view configuration has any non-default filter/sort
 * worth saving. Mirrors the issues-list ``hasActiveIssueFilters`` but works on
 * the URL search shape.
 */
export function hasActiveViewConfig(search: IssueUrlSearch): boolean {
  const params: IssuesQueryParams = {
    search: search.q,
    status_id: search.status_id ?? null,
    priority: search.priority ?? null,
    assignee: search.assignee ?? null,
    label_id: search.label_id ?? null,
    sort: search.sort ?? DEFAULT_SORT_KEY,
  }
  return Boolean(
    params.search?.trim() ||
      params.status_id ||
      params.priority != null ||
      params.assignee ||
      params.label_id ||
      (params.sort && params.sort !== DEFAULT_SORT_KEY),
  )
}
