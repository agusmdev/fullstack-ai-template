import { redirect } from '@tanstack/react-router'
import { isAuthenticated } from './auth'

/**
 * TanStack Router `beforeLoad` guard for protected (authenticated) routes.
 *
 * When the user has no auth token, redirect them to `/login`, preserving the
 * intended destination as a `redirect` search param. The login route reads
 * that param and returns the user to the originally requested route after a
 * successful login (deep-link redirect-after-login).
 *
 * Usage:
 *   export const Route = createFileRoute('/_authed')({
 *     beforeLoad: requireAuthBeforeLoad,
 *     component: ...,
 *   })
 */
export function requireAuthBeforeLoad({
  location,
}: {
  location: { pathname: string }
}) {
  // The auth token lives in localStorage, which is only available in the browser.
  // TanStack Start runs `beforeLoad` during SSR where localStorage is undefined;
  // if we redirected there, every authenticated hard navigation / reload would be
  // bounced to /login (because the server can't see the token). So we skip the
  // guard on the server and let the client enforce it after hydration. This keeps
  // sessions persistent across reload (VAL-AUTH-013) while still gating the route.
  if (typeof window === 'undefined') return

  if (!isAuthenticated()) {
    throw redirect({
      to: '/login',
      search: { redirect: location.pathname },
      replace: true,
    })
  }
}
