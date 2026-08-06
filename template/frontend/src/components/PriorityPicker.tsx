import { Check, ChevronDown } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown'
import { Button } from '@/components/ui/button'
import { PriorityIcon, priorityLabel } from '@/components/PriorityIcon'
import { cn } from '@/lib/utils'
import { PRIORITIES } from '@/types/issue'

interface PriorityPickerProps {
  value: number
  onChange: (priority: number) => void
  disabled?: boolean
  className?: string
}

/**
 * Priority picker — the full 0–4 rank set (Urgent → No priority), defaulting to
 * "No priority" (4) (VAL-ISSUES-005). Controlled: reports the chosen rank.
 */
export function PriorityPicker({
  value,
  onChange,
  disabled,
  className,
}: PriorityPickerProps) {
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
          <PriorityIcon priority={value} />
          <span>{priorityLabel(value)}</span>
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="min-w-[12rem]">
        {PRIORITIES.map((p) => (
          <DropdownMenuItem key={p.value} onClick={() => onChange(p.value)} className="gap-2">
            <PriorityIcon priority={p.value} />
            <span className="flex-1">{p.label}</span>
            {p.value === value && <Check className="h-3.5 w-3.5" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
