import React, { useCallback, useEffect, useRef, useState } from 'react'
import { cn } from '@/lib/utils'

interface DropdownMenuContextValue {
  open: boolean
  setOpen: (open: boolean) => void
}

const DropdownMenuContext = React.createContext<DropdownMenuContextValue | null>(null)

function useDropdownMenuContext() {
  const ctx = React.useContext(DropdownMenuContext)
  if (!ctx) throw new Error('DropdownMenu components must be used within <DropdownMenu>')
  return ctx
}

/**
 * Lightweight, accessible dropdown menu with no external dependency.
 *
 * Closes on outside-click, Escape, and item selection. Renders the trigger as
 * the provided element (it clones children to inject aria attributes and the
 * click handler) and positions the panel absolutely below it.
 */
export function DropdownMenu({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const handlePointerDown = useCallback((e: MouseEvent) => {
    if (!containerRef.current) return
    if (!containerRef.current.contains(e.target as Node)) {
      setOpen(false)
    }
  }, [])

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') setOpen(false)
  }, [])

  useEffect(() => {
    if (!open) return
    document.addEventListener('mousedown', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('mousedown', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [open, handlePointerDown, handleKeyDown])

  return (
    <DropdownMenuContext.Provider value={{ open, setOpen }}>
      <div ref={containerRef} className={cn('relative inline-block', className)}>
        {children}
      </div>
    </DropdownMenuContext.Provider>
  )
}

interface DropdownMenuTriggerProps {
  children: React.ReactElement<{ onClick?: (e: React.MouseEvent) => void; 'aria-expanded'?: boolean; 'aria-haspopup'?: string }>
  className?: string
}

export function DropdownMenuTrigger({ children }: DropdownMenuTriggerProps) {
  const { open, setOpen } = useDropdownMenuContext()
  return React.cloneElement(children, {
    onClick: (e: React.MouseEvent) => {
      e.stopPropagation()
      setOpen(!open)
    },
    'aria-expanded': open,
    'aria-haspopup': 'menu',
  })
}

export function DropdownMenuContent({
  children,
  align = 'start',
  className,
}: {
  children: React.ReactNode
  align?: 'start' | 'end'
  className?: string
}) {
  const { open } = useDropdownMenuContext()
  if (!open) return null
  return (
    <div
      role="menu"
      className={cn(
        'absolute z-50 mt-1 min-w-[12rem] overflow-hidden rounded-md border border-border bg-popover p-1 text-popover-foreground shadow-md',
        align === 'end' ? 'right-0' : 'left-0',
        className,
      )}
    >
      {children}
    </div>
  )
}

interface DropdownMenuItemProps extends React.ComponentProps<'button'> {
  inset?: boolean
}

export function DropdownMenuItem({ className, inset, onClick, ...props }: DropdownMenuItemProps) {
  const { setOpen } = useDropdownMenuContext()
  return (
    <button
      role="menuitem"
      onClick={(e) => {
        onClick?.(e)
        setOpen(false)
      }}
      className={cn(
        'flex w-full cursor-pointer select-none items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground',
        inset && 'pl-8',
        className,
      )}
      {...props}
    />
  )
}

export function DropdownMenuLabel({ className, ...props }: React.ComponentProps<'div'>) {
  return (
    <div
      className={cn('px-2 py-1.5 text-xs font-medium text-muted-foreground', className)}
      {...props}
    />
  )
}

export function DropdownMenuSeparator({ className }: { className?: string }) {
  return <div className={cn('-mx-1 my-1 h-px bg-border', className)} />
}
