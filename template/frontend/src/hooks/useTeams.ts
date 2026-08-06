import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'
import { isAuthenticated } from '@/lib/auth'
import type { TeamsResponse, Team } from '@/types/team'

/**
 * Fetch the teams the authenticated user belongs to (`GET /teams`).
 *
 * Only enabled when a token is present (the workspace sits behind the `_authed`
 * guard). A fresh registration yields exactly one default team; the sidebar uses
 * this to render team identity and scope navigation.
 */
export function useTeams() {
  return useQuery({
    queryKey: queryKeys.teams.list(),
    queryFn: () => api.get<TeamsResponse>(API.TEAMS.LIST),
    enabled: isAuthenticated(),
  })
}

/**
 * Select the first (default) team from a teams query result, or null.
 *
 * A brand-new user has exactly one team auto-created on register. This helper
 * drives the `/` → `/<team-key>/issues` redirect and the sidebar's active team.
 */
export function pickDefaultTeam(teams: Team[] | undefined): Team | null {
  if (!teams || teams.length === 0) return null
  return teams[0]
}
