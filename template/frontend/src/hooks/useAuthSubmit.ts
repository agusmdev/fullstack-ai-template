import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, type NavigateOptions } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'
import { executeAuthSubmit } from '@/features/auth/auth-actions'

export function useAuthSubmit<TPayload extends Record<string, unknown>>(
  endpoint: string,
  successMessage: string,
  errorMessage: string,
  redirect: NavigateOptions = { to: '/' },
) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { login } = useAuth()

  const mutation = useMutation<void, Error, TPayload>({
    mutationFn: (payload: TPayload) =>
      executeAuthSubmit(endpoint, payload, { login, navigate, successMessage, errorMessage, redirect }),
    onSuccess: () => {
      queryClient.invalidateQueries()
    },
  })

  // Swallow the rejection: executeAuthSubmit has already surfaced the failure
  // (toast), and callers hand this promise to react-hook-form's handleSubmit,
  // which rethrows into the DOM event — an unhandled rejection otherwise.
  const submit = (payload: TPayload) => mutation.mutateAsync(payload).catch(() => undefined)
  const isLoading = mutation.isPending

  return { submit, isLoading }
}
