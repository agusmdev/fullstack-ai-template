import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'
import { isAuthenticated } from '@/lib/auth'
import { toastApiError } from '@/lib/error-handler'
import type {
  Issue,
  IssuesResponse,
  CreateIssueInput,
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

/** Page size for the grouped list (fastapi_pagination caps `size` at 100).
 * The filter/sort/pagination feature extends this to true paging/virtualization. */
const ISSUES_PAGE_SIZE = 100

/**
 * Fetch a team's issues (`GET /issues?team_id=`), default-sorted newest-first.
 *
 * Polls on a short interval so remote changes appear within ~8s (VAL-PERF-004,
 * VAL-ISSUES-049). Disabled until a teamId + auth token are present.
 */
export function useIssues(teamId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.issues.list(teamId),
    queryFn: () =>
      api.get<IssuesResponse>(
        `${API.ISSUES.LIST}?team_id=${teamId}&size=${ISSUES_PAGE_SIZE}`,
      ),
    enabled: !!teamId && isAuthenticated(),
    refetchInterval: ISSUES_REFETCH_INTERVAL,
    refetchOnWindowFocus: true,
  })
}

/** Snapshot returned from the create mutation's `onMutate` for rollback. */
interface CreateIssueContext {
  previous: IssuesResponse | undefined
  key: readonly unknown[]
}

/**
 * Create an issue with an **optimistic insert**.
 *
 * - `onMutate`: cancels in-flight refetches, snapshots the cache, and prepends a
 *   temporary issue (placeholder identifier) so the row appears instantly in the
 *   correct status group (VAL-ISSUES-008).
 * - `onError`: rolls the cache back to the snapshot and surfaces an error toast;
 *   the dialog/input stay intact (VAL-ISSUES-009).
 * - `onSettled`: invalidates the list so the real issue (with its server-minted
 *   `TEAM-NN` identifier) reconciles the optimistic row.
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
      const key = queryKeys.issues.list(input.team_id)
      await qc.cancelQueries({ queryKey: key })

      const previous = qc.getQueryData<IssuesResponse>(key)

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

      if (previous) {
        qc.setQueryData<IssuesResponse>(key, {
          ...previous,
          items: [optimistic, ...previous.items],
          total: previous.total + 1,
        })
      }

      return { previous, key }
    },
    onError: (error, _input, context) => {
      if (context?.previous) {
        qc.setQueryData(context.key, context.previous)
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
