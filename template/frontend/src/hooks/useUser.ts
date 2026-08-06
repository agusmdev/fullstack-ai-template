import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'
import { isAuthenticated } from '@/lib/auth'
import type { User } from '@/types/user'

/**
 * Fetch the authenticated user's profile (`GET /users/me`).
 *
 * Only enabled when a token is present (the workspace sits behind the `_authed`
 * guard, so this normally resolves). A token that the backend rejects (expired /
 * invalid) yields a 401, which the api-client turns into a token clear + redirect
 * to `/login` (VAL-AUTH-015).
 */
export function useUser() {
  return useQuery({
    queryKey: queryKeys.users.me(),
    queryFn: () => api.get<User>(API.USERS.ME),
    enabled: isAuthenticated(),
  })
}
