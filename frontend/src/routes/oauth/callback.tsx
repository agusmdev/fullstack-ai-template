import { useEffect } from 'react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'

/**
 * Last step of the OAuth sign-in. The backend finishes the provider handshake
 * and redirects here with the new session: /oauth/callback?session=<session id>.
 */
export const Route = createFileRoute('/oauth/callback')({
  // The session goes to localStorage, which exists only in the browser.
  ssr: false,
  validateSearch: (search: Record<string, unknown>): { session?: string } => ({
    session:
      typeof search['session'] === 'string' && search['session'] ? search['session'] : undefined,
  }),
  component: OAuthCallback,
})

function OAuthCallback() {
  const { session } = Route.useSearch()
  const { login } = useAuth()
  const navigate = useNavigate()

  // In an effect, not in beforeLoad: a redirect during hydration makes the
  // client render a different page than the server sent.
  useEffect(() => {
    if (!session) {
      navigate({ to: '/oauth/error', search: { error: 'missing_session' }, replace: true })
      return
    }
    login(session)
    // replace: keep the session id out of the browser history.
    navigate({ to: '/', replace: true })
  }, [session, login, navigate])

  return <p className="pt-32 text-center text-muted-foreground">Signing you in…</p>
}
