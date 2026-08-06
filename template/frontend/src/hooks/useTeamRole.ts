import { useTeams } from '@/hooks/useTeams'
import { hasRole, type TeamRole } from '@/types/team'

/**
 * Resolve the authenticated user's role in a team (by key), plus derived
 * capability checks.
 *
 * The role is read from the enriched `GET /teams` list response (`my_role`),
 * so no extra request is made. Returns `undefined` while teams are loading or
 * when the key does not match a team the user belongs to (e.g. a cross-team
 * URL — see `useTeamAccessGuard`).
 *
 * Used to gate role-based UI per VAL-CROSS-025: guests are blocked from writes
 * (`canWrite`), members/guests are blocked from admin-only actions such as
 * managing workflow states (`canAdmin`); reads work for everyone.
 */
export function useTeamRole(teamKey: string | undefined) {
  const { data, isLoading } = useTeams()
  const teams = data?.items ?? []
  const team = teamKey ? teams.find((t) => t.key === teamKey) : undefined
  const role: TeamRole | undefined = team?.my_role

  return {
    role,
    isLoading,
    /** At least `member` — may create/edit issues, labels. */
    canWrite: hasRole(role, 'member'),
    /** At least `admin` — may manage members, workflow states, team settings. */
    canAdmin: hasRole(role, 'admin'),
  }
}
