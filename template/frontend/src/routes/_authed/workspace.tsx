import { createFileRoute } from '@tanstack/react-router'
import { useUser } from '@/hooks/useUser'

/**
 * Minimal authenticated workspace landing.
 *
 * This is the route authed users land on after login/register (unless a deep
 * link was preserved). It sits behind the `_authed` guard, so it doubles as the
 * canonical "protected route" for auth assertions:
 *  - unauthenticated direct nav → redirected to `/login` (VAL-AUTH-014)
 *  - a 401 from `/users/me` (bad/expired token) → token cleared → redirected to
 *    `/login` (VAL-AUTH-015)
 *  - reload keeps the user authenticated (token read from localStorage,
 *    VAL-AUTH-013)
 *
 * The full Linear app shell (Sidebar, Topbar, theme toggle, issues board) is
 * built by the `m0-app-shell` and later milestones; this is the authed skeleton.
 */
export const Route = createFileRoute('/_authed/workspace')({
  component: Workspace,
})

function Workspace() {
  const { data: user, isLoading } = useUser()

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-72px)] gap-3 p-8 text-center">
      <h1 className="text-3xl font-bold tracking-tight">Workspace</h1>
      <p className="text-muted-foreground max-w-md">
        {isLoading
          ? 'Loading…'
          : user
            ? `Signed in as ${user.email}. This is your team workspace.`
            : "You're signed in. This is your team workspace."}
      </p>
      <p className="text-xs text-muted-foreground/70 max-w-md">
        The Linear app shell (sidebar, issues, board) arrives with the next milestone.
      </p>
    </div>
  )
}
