import { Check, ChevronDown, UserRound } from 'lucide-react'
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

/** A selectable team member (id + display name). */
export interface MemberOption {
  id: string
  name: string
}

interface AssigneePickerProps {
  value: string | null
  onChange: (assigneeId: string | null) => void
  members: MemberOption[]
  disabled?: boolean
  className?: string
}

/** Renders a member's initials in a small circular avatar. */
function Avatar({ name, className }: { name: string; className?: string }) {
  const initials = name
    .split(/\s+/)
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()
  return (
    <span
      className={cn(
        'flex h-5 w-5 items-center justify-center rounded-full bg-primary/15 text-[10px] font-semibold text-primary',
        className,
      )}
      aria-hidden
    >
      {initials || '?'}
    </span>
  )
}

/**
 * Assignee picker. Defaults to "Unassigned" (null) (VAL-ISSUES-005). Lists the
 * known team members plus an explicit "Unassigned" option. Controlled.
 *
 * NOTE: a full team-members roster endpoint does not exist yet; callers pass the
 * currently-known members (e.g. the signed-in user). This keeps the create flow
 * functional — assigning to the current user persists end-to-end — and will
 * expand once a `/teams/{id}/members` endpoint lands.
 */
export function AssigneePicker({
  value,
  onChange,
  members,
  disabled,
  className,
}: AssigneePickerProps) {
  const current = members.find((m) => m.id === value)

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
          {current ? <Avatar name={current.name} /> : <UserRound className="h-3.5 w-3.5 text-muted-foreground" />}
          <span>{current?.name ?? 'Unassigned'}</span>
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="min-w-[14rem]">
        <DropdownMenuLabel>Assignee</DropdownMenuLabel>
        <DropdownMenuItem onClick={() => onChange(null)} className="gap-2">
          <UserRound className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="flex-1">Unassigned</span>
          {value === null && <Check className="h-3.5 w-3.5" />}
        </DropdownMenuItem>
        {members.length > 0 && <DropdownMenuSeparator />}
        {members.map((m) => (
          <DropdownMenuItem key={m.id} onClick={() => onChange(m.id)} className="gap-2">
            <Avatar name={m.name} />
            <span className="flex-1">{m.name}</span>
            {m.id === value && <Check className="h-3.5 w-3.5" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
