import { toast } from 'sonner'

export function getErrorMessage(error: unknown, fallback = 'An unexpected error occurred'): string {
  if (error instanceof Error) return error.message
  return fallback
}

/**
 * One error toast: `title` says what failed, the description says why.
 * For an ApiError the description is the backend's message (validation errors
 * are already flattened into "field: message" by the API client).
 */
export function toastApiError(error: unknown, title: string) {
  toast.error(title, { description: getErrorMessage(error) })
}
