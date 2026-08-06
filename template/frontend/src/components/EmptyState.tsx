import React from 'react'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  /** Lucide icon component rendered above the title. */
  icon?: React.ComponentType<{ className?: string }>
  title: string
  description?: string
  /** Optional call-to-action (e.g. a "Create issue" button). */
  action?: React.ReactNode
  className?: string
}

/**
 * Intentional empty state used by every list surface when there is no data.
 * Renders an icon, a clear message, an optional description, and an optional CTA
 * — never a blank screen, a spinner, or `undefined`/`NaN`.
 */
export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border p-10 text-center',
        className,
      )}
    >
      {Icon && (
        <div className="flex h-11 w-11 items-center justify-center rounded-full bg-muted text-muted-foreground">
          <Icon className="h-5 w-5" />
        </div>
      )}
      <div className="space-y-1">
        <p className="text-sm font-medium text-foreground">{title}</p>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </div>
      {action && <div className="mt-1">{action}</div>}
    </div>
  )
}
