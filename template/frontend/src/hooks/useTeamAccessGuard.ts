import { useEffect } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { useTeams, pickDefaultTeam } from '@/hooks/useTeams'

/**
 * SPA-side cross-team guard (VAL-CROSS-024).
 *
 * If the active `$team` URL segment does not correspond to a team the user
 * belongs to (e.g. someone manually edits the URL to another team's key),
 * redirect to their default team's issues view. The backend already refuses to
 * serve another team's data (404/403), so this is a UX safeguard that ensures
 * no foreign team's data is ever rendered and the user lands somewhere sane
 * instead of a blank/skeleton screen.
 *
 * No-op while teams are loading or when no team key is present (e.g. the
 * `/workspace` resolver, which has no team segment).
 */
export function useTeamAccessGuard(teamKey: string | undefined) {
  const { data, isLoading } = useTeams()
  const navigate = useNavigate()

  const teams = data?.items ?? []
  const isValid = !teamKey || isLoading || teams.some((t) => t.key === teamKey)

  useEffect(() => {
    if (isValid) return
    const fallback = pickDefaultTeam(teams)
    void navigate({
      to: '/$team/issues',
      params: { team: (fallback ?? { key: '' }).key },
      replace: true,
    })
    // `teams` is derived from `data`; depend on the resolved validity signal.
  }, [isValid, navigate, teams])

  return { isValid }
}
