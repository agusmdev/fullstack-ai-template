import { ArrowUp, ArrowDown, Minus, Signal } from 'lucide-react'
import { cn } from '@/lib/utils'
import { PRIORITIES } from '@/types/issue'

/** Color per priority rank, matching Linear's palette. */
export const PRIORITY_COLORS: Record<number, string> = {
  0: 'text-red-500',
  1: 'text-amber-500',
  2: 'text-yellow-500',
  3: 'text-blue-500',
  4: 'text-muted-foreground',
}

/**
 * Compact priority glyph (no label). Reused by the issue row, the create dialog,
 * and (later) the detail drawer. Renders a muted dash for "No priority".
 */
export function PriorityIcon({ priority, className }: { priority: number; className?: string }) {
  const color = PRIORITY_COLORS[priority] ?? PRIORITY_COLORS[4]
  const iconClass = cn('h-3.5 w-3.5', color, className)

  if (priority === 0) return <Signal className={iconClass} aria-hidden />
  if (priority === 1) return <ArrowUp className={iconClass} aria-hidden />
  if (priority === 2) return <Signal className={cn(iconClass, 'opacity-70')} aria-hidden />
  if (priority === 3) return <ArrowDown className={iconClass} aria-hidden />
  return <Minus className={iconClass} aria-hidden />
}

/** Human label for a priority rank (e.g. "Urgent", "No priority"). */
export function priorityLabel(priority: number): string {
  return PRIORITIES.find((p) => p.value === priority)?.label ?? 'No priority'
}
