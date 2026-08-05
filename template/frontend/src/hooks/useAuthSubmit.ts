import { useState } from 'react'
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
