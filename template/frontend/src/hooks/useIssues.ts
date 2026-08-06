import {
  useInfiniteQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
  type InfiniteData,
} from '@tanstack/react-query'
import { toast } from 'sonner'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'
import { isAuthenticated } from '@/lib/auth'
import { toastApiError } from '@/lib/error-handler'
import {
  ASSIGNEE_UNASSIGNED,
  serializeIssueParams,
  sortKeyToOrderBy,
  type Issue,
  type IssuesQueryParams,
  type IssuesResponse,
  type CreateIssueInput,
} from '@/types/issue'

/** Prefix marking an optimistically-inserted row (before the POST settles). */
export const OPTIMISTIC_ID_PREFIX = 'optimistic-'

/** True for an issue inserted optimistically (placeholder identifier pending). */
export function isOptimisticIssue(issue: Issue): boolean {
  return issue.id.startsWith(OPTIMISTIC_ID_PREFIX)
}

/**
 * Polling interval (ms) — keeps the active list fresh without websockets. */
const ISSUES_REFETCH_INTERVAL = 8000

/**
 * Page size for the grouped list (fastapi_pagination caps `size` at 100). Most
 * teams load in a single fetch; longer lists paginate via "load more"
 * (VAL-ISSUES-029).
 */
const ISSUES_PAGE_SIZE = 50

/**
 * Build the ``GET /issues`` query string from filter/search/sort params + page.
 *
 * All filtering, searching, and sorting is applied **server-side** so the list
 * always matches the backend total exactly (VAL-ISSUES-019–028, VAL-ISSUES-029).
 * Uses URLSearchParams so search terms with spaces/special chars are encoded.
 */
export function buildIssuesQueryString(
  teamId: string,
  params: IssuesQueryParams,
  page: number,
): string {
  const sp = new URLSearchParams()
  sp.set('team_id', teamId)
  sp.set('size', String(ISSUES_PAGE_SIZE))
  sp.set('page', String(page))

  if (params.search?.trim()) sp.set('search', params.search.trim())
  if (params.status_id) sp.set('status_id', params.status_id)
  if (params.priority != null) sp.set('priority', String(params.priority))
  if (params.assignee === ASSIGNEE_UNASSIGNED) {
    sp.set('unassigned', 'true')
  } else if (params.assignee) {
    sp.set('assignee_id', params.assignee)
  }
  if (params.label_id) sp.set('label_id', params.label_id)

  // order_by is a list[str] on the backend (repeated query params); fall back
  // to newest-first when unset.
  for (const field of sortKeyToOrderBy(params.sort)) {
    sp.append('order_by', field)
  }

  return `${API.ISSUES.LIST}?${sp.toString()}`
}

/** The shape React Query uses to cache an infinite (paginated) query. */
type IssuesInfiniteData = InfiniteData<IssuesResponse, number>

/**
 * Flatten the paginated cache into the issues loaded so far (all pages).
 */
export function flattenIssues(data: IssuesInfiniteData | undefined): Issue[] {
  return data?.pages.flatMap((p) => p.items) ?? []
}

/**
 * The full filtered total (the same across every page from fastapi_pagination).
 */
export function issuesTotal(data: IssuesInfiniteData | undefined): number {
  return data?.pages[0]?.total ?? 0
}

/**
 * Fetch a team's issues with server-side filter/search/sort + "load more"
 * pagination (`useInfiniteQuery`).
 *
 * - Filters/search/sort are query params, so distinct states are cached
 *   separately and the list matches the backend total exactly.
 * - Polls on a short interval so remote changes appear within ~8s
 *   (VAL-PERF-004, VAL-ISSUES-049). Disabled until a teamId + token are present.
 * - Each page fetches {@link ISSUES_PAGE_SIZE} issues; `fetchNextPage` loads the
 *   next page for long lists (VAL-ISSUES-029).
 */
export function useIssues(teamId: string | undefined, params: IssuesQueryParams = {}) {
  const paramsKey = serializeIssueParams(params)
  return useInfiniteQuery<IssuesResponse, Error, IssuesInfiniteData, unknown[], number>({
    queryKey: queryKeys.issues.list(teamId, paramsKey),
    queryFn: ({ pageParam }) =>
      api.get<IssuesResponse>(buildIssuesQueryString(teamId!, params, pageParam)),
    initialPageParam: 1,
    getNextPageParam: (lastPage) =>
      lastPage.page < lastPage.pages ? lastPage.page + 1 : undefined,
    enabled: !!teamId && isAuthenticated(),
    // Keep the previous page data visible while a new filter/search/sort query
    // loads, so changing filters never flashes the skeleton/empty state.
    placeholderData: keepPreviousData,
    refetchInterval: ISSUES_REFETCH_INTERVAL,
    refetchOnWindowFocus: true,
  })
}

/** Snapshot of every matching list cache entry, for rollback on create error. */
interface CreateIssueContext {
  previous: Array<readonly [readonly unknown[], IssuesInfiniteData | undefined]>
}

/**
 * Create an issue with an **optimistic insert**.
 *
 * - `onMutate`: cancels in-flight refetches, snapshots every matching list cache
 *   entry (any filter/sort variant), and prepends a temporary issue (placeholder
 *   identifier) to the first page of the **unfiltered default** view so the row
 *   appears instantly in the correct status group (VAL-ISSUES-008). Filtered
 *   views are left untouched (a newly-created issue may not match the active
 *   filter); they reconcile via the post-settle invalidation.
 * - `onError`: rolls every snapshot back and surfaces an error toast; the
 *   dialog/input stay intact (VAL-ISSUES-009).
 * - `onSettled`: invalidates all list variants so the real issue (with its
 *   server-minted `TEAM-NN` identifier) reconciles the optimistic row.
 */
export function useCreateIssue() {
  const qc = useQueryClient()

  return useMutation<Issue, Error, CreateIssueInput, CreateIssueContext>({
    mutationFn: (input) => {
      // Build the API payload from the serializable fields only (drop the
      // optimistic-only labels used for instant display).
      const payload = {
        team_id: input.team_id,
        title: input.title,
        description: input.description,
        status_id: input.status_id,
        priority: input.priority,
        assignee_id: input.assignee_id,
        label_ids: input.label_ids,
      }
      return api.post<Issue>(API.ISSUES.CREATE, payload)
    },
    onMutate: async (input) => {
      // Prefix matches every list variant for this team (any filter/sort/page).
      const prefix = queryKeys.issues.list(input.team_id)
      await qc.cancelQueries({ queryKey: prefix })

      // Snapshot every matching list cache entry for rollback (key + data).
      const previous = qc.getQueriesData<IssuesInfiniteData>({ queryKey: prefix })

      const optimistic: Issue = {
        id: `optimistic-${crypto.randomUUID()}`,
        team_id: input.team_id,
        identifier: '',
        title: input.title,
        description: input.description ?? null,
        status_id: input.status_id ?? '',
        priority: input.priority,
        assignee_id: input.assignee_id ?? null,
        creator_id: '',
        project_id: null,
        cycle_id: null,
        parent_id: null,
        sort_order: 0,
        estimate: null,
        due_date: null,
        labels: (input.optimisticLabels ?? []).map((l) => ({
          id: l.id,
          name: l.name,
          color: l.color,
        })),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      // Only prepend to the **default (unfiltered) view** — there a new issue is
      // always expected at the top (VAL-ISSUES-008). Filtered views may not
      // match the new issue; they reconcile via the settle invalidation.
      // Key shape: ['issues', 'list', teamId, paramsKey] where '' = default.
      for (const [key, data] of previous) {
        if (!data || data.pages.length === 0) continue
        const paramsKey = key[3]
        if (paramsKey !== '' && paramsKey !== undefined) continue
        qc.setQueryData<IssuesInfiniteData>(key, prependOptimistic(data, optimistic))
      }

      return { previous }
    },
    onError: (error, _input, context) => {
      if (context?.previous) {
        for (const [key, data] of context.previous) {
          qc.setQueryData(key, data)
        }
      }
      toastApiError(error, 'Failed to create issue')
    },
    onSuccess: () => {
      toast.success('Issue created')
    },
    onSettled: (_data, _error, input) => {
      void qc.invalidateQueries({ queryKey: queryKeys.issues.list(input.team_id) })
    },
  })
}

/**
 * Prepend an optimistic issue to the first page of an infinite cache entry,
 * **only** when that entry represents the unfiltered default view (params key
 * empty). Filtered views are left to reconcile via the settle invalidation.
 */
function prependOptimistic(
  old: IssuesInfiniteData,
  optimistic: Issue,
): IssuesInfiniteData {
  const first = old.pages[0]
  const updated: IssuesResponse = {
    ...first,
    items: [optimistic, ...first.items],
    total: first.total + 1,
  }
  return {
    ...old,
    pages: [updated, ...old.pages.slice(1)],
  }
}
