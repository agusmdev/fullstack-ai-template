import { useState } from 'react'
import { useNavigate, type NavigateOptions } from '@tanstack/react-router'
import { toast } from 'sonner'
import { api } from '@/lib/api-client'
import { useAuth } from '@/contexts/AuthContext'
import { toastApiError } from '@/lib/error-handler'
import type { AuthSessionResponse } from '@/types/auth'

/**
 * Core auth submit logic — extracted for unit testing without React mounting.
 * Handles the api.post → login → toast → navigate orchestration.
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
  }
}

export function useAuthSubmit<TPayload extends Record<string, unknown>>(
  endpoint: string,
  successMessage: string,
  errorMessage: string,
  redirect: NavigateOptions = { to: '/' },
) {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [isLoading, setIsLoading] = useState(false)

  const submit = async (payload: TPayload) => {
    setIsLoading(true)
    try {
      await executeAuthSubmit(endpoint, payload, { login, navigate, successMessage, errorMessage, redirect })
    } finally {
      setIsLoading(false)
    }
  }

  return { submit, isLoading }
}
