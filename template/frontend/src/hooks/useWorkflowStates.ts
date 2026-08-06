import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'
import { isAuthenticated } from '@/lib/auth'
import type { WorkflowStatesResponse } from '@/types/workflow-state'

/**
 * Fetch a team's workflow states (`GET /workflow-states?team_id=`), ordered by
 * `position`. These drive the canonical status grouping order (Backlog →
 * Unstarted → Started → Completed → Canceled) and populate the status picker.
 *
 * Only enabled when a teamId and auth token are present.
 */
export function useWorkflowStates(teamId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.workflowStates.list(teamId),
    queryFn: () =>
      api.get<WorkflowStatesResponse>(`${API.WORKFLOW_STATES.LIST}?team_id=${teamId}&size=100`),
    enabled: !!teamId && isAuthenticated(),
    staleTime: 5 * 60 * 1000, // workflow states rarely change; cache 5 min
  })
}
