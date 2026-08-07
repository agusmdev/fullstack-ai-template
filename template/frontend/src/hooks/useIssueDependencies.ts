import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import { toast } from 'sonner'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'
import { isAuthenticated } from '@/lib/auth'
import { toastApiError } from '@/lib/error-handler'
import type { IssuesResponse } from '@/types/issue'
import type {
  IssueDependency,
  IssueDependenciesResponse,
  CreateIssueDependencyInput,
  DeleteIssueDependencyInput,
} from '@/types/issue-dependency'

/** Polling interval (ms) — keeps reciprocal dependency lists fresh. */
const DEPS_REFETCH_INTERVAL = 8000

/**
 * Split a flat dependency list into the two reciprocal views for an issue.
 *
 * For "A blocks B": from A's perspective this is a **blocking** entry (A blocks
 * B); from B's perspective it is a **blockedBy** entry (B is blocked by A)
 * (VAL-DEPS-002). A single dependency record appears in exactly one of the two
 * lists for any given issue.
 */
export function splitDependencies(
  deps: IssueDependency[],
  issueId: string,
): { blocking: IssueDependency[]; blockedBy: IssueDependency[] } {
  const blocking: IssueDependency[] = []
  const blockedBy: IssueDependency[] = []
  for (const dep of deps) {
    if (dep.blocker_id === issueId) blocking.push(dep)
    else if (dep.blocked_id === issueId) blockedBy.push(dep)
  }
  return { blocking, blockedBy }
}

/**
 * Fetch every dependency involving an issue (either side — reciprocal).
 *
 * Polls on a short interval so a dependency added/removed elsewhere reconciles
 * on both issues without a manual refresh (VAL-DEPS-002, VAL-PERF-004).
 */
export function useIssueDependencies(
  issueId: string | undefined,
  teamId: string | undefined,
) {
  return useQuery<IssueDependenciesResponse, Error>({
    queryKey: queryKeys.issueDependencies.forIssue(issueId!),
    queryFn: () => {
      const sp = new URLSearchParams()
      sp.set('issue_id', issueId!)
      sp.set('size', '100')
      return api.get<IssueDependenciesResponse>(
        `${API.ISSUE_DEPENDENCIES.LIST}?${sp.toString()}`,
      )
    },
    enabled: !!issueId && !!teamId && isAuthenticated(),
    refetchInterval: DEPS_REFETCH_INTERVAL,
    refetchOnWindowFocus: true,
  })
}

/**
 * Fetch the team's issues to populate the dependency picker. Disabled until the
 * picker is opened. The backend scopes by ``team_id`` so only same-team issues
 * are offered (VAL-DEPS-005).
 */
export function useTeamIssuesForPicker(teamId: string | undefined, enabled = false) {
  return useQuery<IssuesResponse, Error>({
    queryKey: ['issues', 'teamPicker', teamId],
    queryFn: () => {
      const sp = new URLSearchParams()
      sp.set('team_id', teamId!)
      sp.set('size', '100')
      return api.get<IssuesResponse>(`${API.ISSUES.LIST}?${sp.toString()}`)
    },
    enabled: !!teamId && enabled && isAuthenticated(),
    staleTime: 10_000,
  })
}

/**
 * Create a 'blocks' dependency ("A blocks B").
 *
 * Surfaces a clear error on a cycle (409) or self/cross-team rejection
 * (VAL-DEPS-003, VAL-DEPS-005). On success, invalidates the dependency caches
 * for both endpoints so reciprocal display updates on both issues.
 */
export function useCreateIssueDependency() {
  const qc = useQueryClient()

  return useMutation<IssueDependency, Error, CreateIssueDependencyInput>({
    mutationFn: (input) =>
      api.post<IssueDependency>(API.ISSUE_DEPENDENCIES.CREATE, {
        blocker_id: input.blocker_id,
        blocked_id: input.blocked_id,
      }),
    onSuccess: (dep) => {
      toast.success('Dependency added')
      // Invalidate both endpoints' caches so reciprocal display reconciles
      // immediately (VAL-DEPS-002).
      void qc.invalidateQueries({
        queryKey: queryKeys.issueDependencies.forIssue(dep.blocker_id),
      })
      void qc.invalidateQueries({
        queryKey: queryKeys.issueDependencies.forIssue(dep.blocked_id),
      })
    },
    onError: (error, _input) => {
      // 409 = circular dependency — surface the backend's clear message.
      toastApiError(error, 'Could not add dependency')
    },
  })
}

/**
 * Delete a dependency by ID. Removing the single record detaches it from both
 * issues (VAL-DEPS-004); the invalidation refreshes both reciprocal views.
 */
export function useDeleteIssueDependency() {
  const qc = useQueryClient()

  return useMutation<void, Error, DeleteIssueDependencyInput>({
    mutationFn: (input) =>
      api.delete<void>(API.ISSUE_DEPENDENCIES.DETAIL(input.id)),
    onSuccess: () => {
      toast.success('Dependency removed')
    },
    onError: (error) => {
      toastApiError(error, 'Could not remove dependency')
    },
    onSettled: () => {
      // Refresh every dependency view (the deleted record affected two issues).
      void qc.invalidateQueries({ queryKey: queryKeys.issueDependencies.all })
    },
  })
}
