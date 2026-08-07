import { useEffect } from 'react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useTeams, pickDefaultTeam } from '@/hooks/useTeams'
import { LoadingSkeleton } from '@/components/LoadingSkeleton'
import { ErrorState } from '@/components/ErrorState'

/**
 * Workspace landing — resolves the user's default team and redirects into its
 * issues view (`/$team/issues`). Authed users land here from `/` and after
 * login (unless a deep link was preserved). While teams load we show a skeleton;
 * a fresh registration yields exactly one default team.
 */
export const Route = createFileRoute('/_authed/workspace')({
  component: Workspace,
})

function Workspace() {
  const { data, isLoading, isError, error, refetch } = useTeams()
  const navigate = useNavigate()
  const defaultTeam = pickDefaultTeam(data?.items)

  useEffect(() => {
    if (defaultTeam) {
      void navigate({
        to: '/$team/issues',
        params: { team: defaultTeam.key },
        replace: true,
      })
    }
  }, [defaultTeam, navigate])

  if (isLoading) {
    return (
      <div className="p-6">
        <LoadingSkeleton rows={3} />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="p-6">
        <ErrorState error={error} onRetry={() => refetch()} title="Couldn't load your workspace" />
      </div>
    )
  }

  // Teams loaded but none found (shouldn't happen for authed users).
  if (!defaultTeam) {
    return (
      <div className="p-6">
        <ErrorState
          error={new Error('No teams found for this account')}
          title="No workspace available"
        />
      </div>
    )
  }

  // Redirect is in flight; render the skeleton in the meantime.
  return (
    <div className="p-6">
      <LoadingSkeleton rows={3} />
    </div>
  )
}
