import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'
import { isAuthenticated } from '@/lib/auth'
import type { ActivityResponse } from '@/types/activity'

/** Polling interval (ms) — keeps the feed fresh without websockets. */
const ACTIVITY_REFETCH_INTERVAL = 8000

/** Page size for the activity feed (fastapi_pagination caps `size` at 100). */
const ACTIVITY_PAGE_SIZE = 50

/**
 * Fetch the read-only activity feed for an issue
 * (`GET /activity?issue_id=<id>`).
 *
 * The backend defaults to newest-first (``order_by=-created_at``) so the most
 * recently generated entry renders at the top. Polls on a short interval so a
 * new entry appears automatically within the polling window after a mutation —
 * no manual reload (VAL-ACTIVITY-008). The feed is read-only; there is no
 * composer (VAL-ACTIVITY-009).
 */
export function useActivity(issueId: string | undefined, teamId: string | undefined) {
  return useQuery<ActivityResponse, Error>({
    queryKey: queryKeys.activity.forIssue(issueId!),
    queryFn: () => {
      const sp = new URLSearchParams()
      sp.set('issue_id', issueId!)
      sp.set('size', String(ACTIVITY_PAGE_SIZE))
      return api.get<ActivityResponse>(`${API.ACTIVITY.LIST}?${sp.toString()}`)
    },
    enabled: !!issueId && !!teamId && isAuthenticated(),
    refetchInterval: ACTIVITY_REFETCH_INTERVAL,
    refetchOnWindowFocus: true,
  })
}
