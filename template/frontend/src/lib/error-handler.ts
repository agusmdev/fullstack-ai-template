import { toast } from 'sonner'
import { ApiError } from './api-client'

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
    description: error instanceof Error ? error.message : 'An unexpected error occurred'
  })
}
