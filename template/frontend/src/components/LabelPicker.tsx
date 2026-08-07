import { Check, ChevronDown, Tag } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown'
import { Button } from '@/components/ui/button'
import { StatusDot } from '@/components/StatusDot'
import { cn } from '@/lib/utils'
import type { Label } from '@/types/label'

interface LabelPickerProps {
  value: string[]
  onChange: (labelIds: string[]) => void
  labels: Label[]
  disabled?: boolean
  className?: string
}

/**
 * Multi-select label picker. Defaults to no labels (VAL-ISSUES-005). Toggling a
 * label adds/removes its id from the selection; the dropdown stays open so
 * multiple can be picked in one go. Controlled.
 */
export function LabelPicker({
  value,
  onChange,
  labels,
  disabled,
  className,
}: LabelPickerProps) {
  const toggle = (id: string) => {
    onChange(value.includes(id) ? value.filter((v) => v !== id) : [...value, id])
  }

  const selectedCount = value.length

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
          <Tag className="h-3.5 w-3.5 text-muted-foreground" />
          <span>{selectedCount > 0 ? `${selectedCount} label${selectedCount > 1 ? 's' : ''}` : 'Labels'}</span>
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="min-w-[14rem]">
        <DropdownMenuLabel>Labels</DropdownMenuLabel>
        {labels.length === 0 ? (
          <div className="px-2 py-1.5 text-sm text-muted-foreground">No labels yet</div>
        ) : (
          labels.map((label) => {
            const selected = value.includes(label.id)
            return (
              <button
                key={label.id}
                type="button"
                role="menuitemcheckbox"
                aria-checked={selected}
                onClick={() => toggle(label.id)}
                className="flex w-full cursor-pointer select-none items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground"
              >
                <StatusDot color={label.color} />
                <span className="flex-1">{label.name}</span>
                {selected && <Check className="h-3.5 w-3.5" />}
              </button>
            )
          })
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
