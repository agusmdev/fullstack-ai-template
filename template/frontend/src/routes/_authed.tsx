import { useEffect } from 'react'
import { createFileRoute, Outlet, useNavigate } from '@tanstack/react-router'
import { isAuthenticated } from '@/lib/auth'
import { requireAuthBeforeLoad } from '@/lib/auth-guard'

/**
 * Pathless layout route that guards every authenticated surface.
 *
 * Auth is enforced in two complementary places:
 *
 * 1. `beforeLoad` (requireAuthBeforeLoad) — runs on client soft-navigation
 *    (clicking a link) and redirects instantly with no flash. It is skipped
 *    during SSR because the auth token lives in localStorage, which is not
 *    available on the server.
 *
 * 2. The `useEffect` below — after hydration, if a hard navigation / reload
 *    landed an unauthenticated user on a protected route (bypassing the
 *    SSR-skipped beforeLoad), redirect them to `/login`, preserving the
 *    intended destination as a `redirect` search param.
 *
 * Together these satisfy: protected-route redirect (VAL-AUTH-014), deep-link
 * redirect-after-login (VAL-AUTH-016), and session-persists-across-reload
 * (VAL-AUTH-013, where the effect is a no-op for authenticated users).
 *
 * Note: the visual Linear app shell (Sidebar, Topbar, theme toggle) is added by
 * the `m0-app-shell` feature; this layout only enforces the auth boundary.
 */
export const Route = createFileRoute('/_authed')({
  beforeLoad: requireAuthBeforeLoad,
  component: AuthedLayout,
})

function AuthedLayout() {
  const navigate = useNavigate()

  useEffect(() => {
    if (!isAuthenticated()) {
      void navigate({
        to: '/login',
        search: { redirect: window.location.pathname },
        replace: true,
      })
    }
  }, [navigate])

  return <Outlet />
}
