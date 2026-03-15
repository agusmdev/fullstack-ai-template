import { useState } from 'react'
import { useNavigate, type NavigateOptions } from '@tanstack/react-router'
import { toast } from 'sonner'
import { api } from '@/lib/api-client'
import { useAuth } from '@/contexts/AuthContext'
import { handleApiError } from '@/lib/error-handler'
import type { AuthSessionResponse } from '@/types/auth'

export function useAuthSubmit(
  endpoint: string,
  successMessage: string,
  errorMessage: string,
  redirect: NavigateOptions = { to: '/' },
) {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [isLoading, setIsLoading] = useState(false)

  const submit = async (payload: Record<string, string>) => {
    setIsLoading(true)
    try {
      const result = await api.post<AuthSessionResponse>(endpoint, payload)
      login(result)
      toast.success(successMessage)
      navigate(redirect)
    } catch (err) {
      handleApiError(err, errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  return { submit, isLoading }
}
