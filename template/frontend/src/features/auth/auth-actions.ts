import { type NavigateOptions } from '@tanstack/react-router'
import { toast } from 'sonner'
import { api } from '@/lib/api-client'
import { toastApiError } from '@/lib/error-handler'
import type { AuthSessionResponse } from '@/types/auth'

/**
 * Core auth submit logic — a framework-agnostic orchestrator extracted from the
 * useAuthSubmit hook so it can be unit-tested without React mounting.
 *
 * Handles the api.post → login → toast → navigate sequence. On failure the
 * error is surfaced via toastApiError AND re-thrown so callers (e.g.
 * useAuthSubmit / useMutation) can observe rejection and react accordingly.
 * Lives in features/auth/ (not hooks/) because it is a plain async function
 * that uses no React APIs.
 */
export async function executeAuthSubmit(
  endpoint: string,
  payload: Record<string, unknown>,
  deps: {
    login: (token: string) => void
    navigate: (opts: NavigateOptions) => void
    successMessage: string
    errorMessage: string
    redirect: NavigateOptions
  },
): Promise<void> {
  try {
    const result = await api.post<AuthSessionResponse>(endpoint, payload)
    deps.login(result.id)
    toast.success(deps.successMessage)
    deps.navigate(deps.redirect)
  } catch (err) {
    toastApiError(err, deps.errorMessage)
    throw err
  }
}
