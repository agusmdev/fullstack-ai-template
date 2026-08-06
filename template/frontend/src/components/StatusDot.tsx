import { cn } from '@/lib/utils'

/**
 * Coloured status dot used in group headers, status pickers, and (later) the
 * board. Falls back to a neutral colour when the state has none.
 */
export function StatusDot({
  color,
  className,
  type,
}: {
  color?: string | null
  className?: string
  type?: string
}) {
  // Terminal states (completed/canceled) get a subtle ring to distinguish them.
  const isTerminal = type === 'completed' || type === 'canceled'
  return (
    <span
      className={cn('inline-block h-2.5 w-2.5 shrink-0 rounded-full', className)}
      style={{
        backgroundColor: color ?? 'var(--muted-foreground)',
        opacity: isTerminal ? 0.7 : 1,
      }}
      aria-hidden
    />
  )
}
