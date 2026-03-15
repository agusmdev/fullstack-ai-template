import { toast } from 'sonner'
import { ApiError } from './api-client'

/**
 * Centralized error handler for API errors
 * @param error - The error to handle
 * @param fallbackMessage - The fallback message to display if the error is not an ApiError
 */
export function handleApiError(error: unknown, fallbackMessage: string) {
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
    description: error instanceof Error ? error.message : 'An unexpected error occurred'
  })
}
