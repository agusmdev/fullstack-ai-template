import { Check, ChevronDown, Repeat2, Ban } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { cyclePhase, type Cycle } from '@/types/cycle'

interface CyclePickerProps {
  /** Current cycle_id of the issue (null = no cycle). */
  value: string | null
  onChange: (cycleId: string | null) => void
  /** The team's cycles. */
  cycles: Cycle[]
  disabled?: boolean
  className?: string
}

const PHASE_STYLES: Record<string, string> = {
  active: 'bg-primary/10 text-primary',
  upcoming: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
  past: 'bg-muted text-muted-foreground',
}

/**
 * Cycle picker — assigns an issue to a cycle or clears the assignment.
 *
 * Lists the team's cycles plus an explicit "No cycle" option to detach.
 * Selecting a cycle reports its id back via `onChange`; selecting "No cycle"
 * reports ``null`` (VAL-CYCLES-005). Reassigning moves the issue (it belongs
 * to at most one cycle — VAL-CYCLES-007).
 *
 * Controlled: the caller persists the change (typically via `useUpdateIssue`
 * with an optimistic patch that propagates the cycle badge everywhere).
 */
export function CyclePicker({
  value,
  onChange,
  cycles,
  disabled,
  className,
}: CyclePickerProps) {
  const current = cycles.find((c) => c.id === value)

  return (
    <DropdownMenu>
      <DropdownMenuTrigger>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={disabled}
          className={cn('gap-2 font-normal', className)}
        >
          {current ? (
            <Repeat2 className="h-3.5 w-3.5 text-muted-foreground" />
          ) : (
            <Repeat2 className="h-3.5 w-3.5 text-muted-foreground/50" />
          )}
          <span>{current?.name ?? 'No cycle'}</span>
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="min-w-[16rem]">
        <DropdownMenuLabel>Cycle</DropdownMenuLabel>
        <DropdownMenuItem onClick={() => onChange(null)} className="gap-2">
          <Ban className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="flex-1">No cycle</span>
          {value === null && <Check className="h-3.5 w-3.5" />}
        </DropdownMenuItem>
        {cycles.length > 0 && <DropdownMenuSeparator />}
        {cycles.map((c) => {
          const phase = cyclePhase(c)
          return (
            <DropdownMenuItem
              key={c.id}
              onClick={() => onChange(c.id)}
              className="gap-2"
            >
              <Repeat2 className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="flex-1 truncate">{c.name}</span>
              <span
                className={cn(
                  'rounded-full px-1.5 py-0.5 text-[9px] font-medium uppercase',
                  PHASE_STYLES[phase],
                )}
              >
                {phase}
              </span>
              {c.id === value && <Check className="h-3.5 w-3.5" />}
            </DropdownMenuItem>
          )
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
