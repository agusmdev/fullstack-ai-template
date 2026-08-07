import { cn } from '@/lib/utils'

/**
 * Skeleton placeholder for loading states. Renders an animated shimmer block
 * sized via className. Used by LoadingSkeleton and every async surface.
 */
function Skeleton({ className, ...props }: React.ComponentProps<'div'>) {
  return (
    <div
      data-slot="skeleton"
      className={cn('animate-pulse rounded-md bg-muted', className)}
      {...props}
    />
  )
}

export { Skeleton }
