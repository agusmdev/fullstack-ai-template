import { useEffect } from 'react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { isAuthenticated } from '@/lib/auth'
import { requireAuthBeforeLoad } from '@/lib/auth-guard'
import { useIsHydrated } from '@/hooks/useIsHydrated'
import { AppShell } from '@/components/AppShell'
import { AppShellSkeleton } from '@/components/AppShellSkeleton'

/**
 * Pathless layout route that guards every authenticated surface and renders the
 * Linear workspace shell (Sidebar + Topbar) around the routed page.
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
 * Hydration gate: until hydration completes we render a neutral
 * `<AppShellSkeleton>` (see `useIsHydrated`). Because the server cannot read the
 * localStorage auth token, rendering the full AppShell during SSR would diverge
 * from the client's first paint and emit a React hydration-mismatch warning
 * (VAL-WORKSPACE-005). The skeleton contains no client-only state, so SSR and the
 * first client paint are byte-identical; the real `<AppShell>` renders afterward.
 */
export const Route = createFileRoute('/_authed')({
  beforeLoad: requireAuthBeforeLoad,
  component: AuthedLayout,
})

function AuthedLayout() {
  const navigate = useNavigate()
  const isHydrated = useIsHydrated()

  useEffect(() => {
    if (!isAuthenticated()) {
      void navigate({
        to: '/login',
        search: { redirect: window.location.pathname },
        replace: true,
      })
    }
  }, [navigate])

  // Gate the authenticated shell behind hydration. During SSR the server cannot
  // read the localStorage auth token, so any auth/data-dependent rendering in
  // the AppShell subtree would diverge from the client's first paint and trigger
  // a React hydration-mismatch warning. By rendering a neutral, client-state-free
  // skeleton until hydration completes, the server HTML and the initial client
  // render are byte-identical. Once hydrated, the real AppShell (and its data
  // queries) renders, and the effect above enforces the auth redirect for an
  // unauthenticated hard navigation (VAL-AUTH-014). Authenticated reloads stay put
  // (VAL-AUTH-013).
  if (!isHydrated) {
    return <AppShellSkeleton />
  }

  return <AppShell />
}
