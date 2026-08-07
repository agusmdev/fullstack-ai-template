import { type ReactNode } from 'react'
import { cn } from '@/lib/utils'

/**
 * A small keyboard-key badge used to surface shortcut hints next to the actions
 * they trigger (VAL-SHORTCUTS-006), e.g. "⌘K", "C", "G I".
 *
 * Consistent styling for inline hints (Topbar search, New issue button, sidebar
 * nav) and the shortcuts help reference.
 */
export function Kbd({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <kbd
      className={cn(
        'inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded border border-border bg-muted/60 px-1 font-sans text-[10px] font-medium text-muted-foreground',
        className,
      )}
    >
      {children}
    </kbd>
  )
}
