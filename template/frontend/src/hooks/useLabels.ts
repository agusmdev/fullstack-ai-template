import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'
import { isAuthenticated } from '@/lib/auth'
import type { LabelsResponse } from '@/types/label'

/**
 * Fetch a team's labels (`GET /labels?team_id=`). Populates the label picker.
 *
 * Only enabled when a teamId and auth token are present.
 */
export function useLabels(teamId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.labels.list(teamId),
    queryFn: () => api.get<LabelsResponse>(`${API.LABELS.LIST}?team_id=${teamId}&size=100`),
    enabled: !!teamId && isAuthenticated(),
    staleTime: 5 * 60 * 1000,
  })
}
