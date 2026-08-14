import { toast } from 'sonner'
import { ApiError } from './api-client'

export function getErrorMessage(error: unknown, fallback = 'An unexpected error occurred'): string {
  if (error instanceof Error) return error.message
  return fallback
}

export function toastApiError(error: unknown, fallbackMessage: string) {
  if (error instanceof ApiError) {
    if (error.fields) {
      Object.entries(error.fields).forEach(([field, messages]) => {
        toast.error(`${field}: ${messages.join(', ')}`)
      })
      return
    }
    toast.error(fallbackMessage, { description: error.message })
    return
  }
  toast.error(fallbackMessage, {
    description: getErrorMessage(error),
  })
}
