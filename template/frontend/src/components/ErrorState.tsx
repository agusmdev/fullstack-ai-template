import { AlertTriangle, RotateCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { getErrorMessage } from '@/lib/error-handler'
import { cn } from '@/lib/utils'

interface ErrorStateProps {
  /** The error caught from a query/mutation. */
  error: unknown
  /** Optional retry handler — renders a "Try again" button when provided. */
  onRetry?: () => void
  /** Optional custom title; defaults to a generic message. */
  title?: string
  className?: string
}

/**
 * Graceful error surface for failed async operations (e.g. backend unreachable,
 * 5xx responses). Prevents white-screens and uncaught exceptions by rendering a
 * friendly message + optional retry, instead of crashing the view.
 */
export function ErrorState({ error, onRetry, title, className }: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-10 text-center',
        className,
      )}
    >
      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-destructive/10 text-destructive">
        <AlertTriangle className="h-5 w-5" />
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium text-foreground">
          {title ?? 'Something went wrong'}
        </p>
        <p className="text-sm text-muted-foreground">
          {getErrorMessage(error, 'An unexpected error occurred')}
        </p>
      </div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry} className="mt-1">
          <RotateCw className="h-4 w-4" />
          Try again
        </Button>
      )}
    </div>
  )
}
