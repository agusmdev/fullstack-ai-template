import { Check, ChevronDown } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown'
import { Button } from '@/components/ui/button'
import { StatusDot } from '@/components/StatusDot'
import { cn } from '@/lib/utils'
import type { WorkflowState } from '@/types/workflow-state'

interface StatusPickerProps {
  value: string | null
  onChange: (statusId: string | null) => void
  states: WorkflowState[]
  disabled?: boolean
  className?: string
}

/**
 * Status picker — offers all of the team's workflow states (all five canonical
 * types: backlog / unstarted / started / completed / canceled), ordered by
 * position (VAL-ISSUES-041, VAL-ISSUES-016). Controlled: reports the chosen
 * status id back via `onChange`.
 */
export function StatusPicker({
  value,
  onChange,
  states,
  disabled,
  className,
}: StatusPickerProps) {
  const current = states.find((s) => s.id === value) ?? states[0]

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
          {current && <StatusDot color={current.color} type={current.type} />}
          <span>{current?.name ?? 'Status'}</span>
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="min-w-[14rem]">
        {states.map((state) => (
          <DropdownMenuItem
            key={state.id}
            onClick={() => onChange(state.id)}
            className="gap-2"
          >
            <StatusDot color={state.color} type={state.type} />
            <span className="flex-1">{state.name}</span>
            {state.id === value && <Check className="h-3.5 w-3.5" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
