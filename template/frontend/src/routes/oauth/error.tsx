import { createFileRoute, Link } from '@tanstack/react-router'
import { AuthFormShell } from '@/components/AuthFormShell'

// Codes sent by the backend's OAuth callback (`/oauth/error?error=<code>`) and
// by the /oauth/callback route.
const MESSAGES = new Map([
  ['access_denied', 'Sign-in was cancelled at the provider.'],
  ['missing_code', 'The sign-in provider did not send an authorization code.'],
  ['unsupported_provider', 'This sign-in provider is not supported.'],
  ['inactive_user', 'This account is not allowed to sign in.'],
  ['missing_session', 'The sign-in response did not include a session.'],
])
const FALLBACK_MESSAGE = 'Something went wrong while signing you in.'

export const Route = createFileRoute('/oauth/error')({
  validateSearch: (search: Record<string, unknown>): { error?: string } => ({
    error: typeof search['error'] === 'string' ? search['error'] : undefined,
  }),
  component: OAuthError,
})

function OAuthError() {
  const { error } = Route.useSearch()
  const message = (error && MESSAGES.get(error)) || FALLBACK_MESSAGE

  return (
    <AuthFormShell
      title="Sign-in failed"
      description={message}
      footer={
        <div className="mt-4 text-center text-sm">
          <Link
            to="/login"
            className="text-primary hover:text-primary/80 underline-offset-4 hover:underline"
          >
            Back to sign in
          </Link>
        </div>
      }
    >
      {error && (
        <p className="text-center text-xs text-muted-foreground">
          Error code: <code>{error}</code>
        </p>
      )}
    </AuthFormShell>
  )
}
