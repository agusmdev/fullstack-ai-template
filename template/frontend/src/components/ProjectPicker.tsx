import { Check, ChevronDown, Folder, Ban } from 'lucide-react'
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
import type { Project } from '@/types/project'

interface ProjectPickerProps {
  /** Current project_id of the issue (null = no project). */
  value: string | null
  onChange: (projectId: string | null) => void
  /** The team's projects. */
  projects: Project[]
  disabled?: boolean
  className?: string
}

/**
 * Project picker — assigns an issue to a project or clears the assignment.
 *
 * Lists the team's projects plus an explicit "No project" option to detach.
 * Selecting a project reports its id back via `onChange`; selecting "No
 * project" reports ``null`` (VAL-PROJECTS-007, VAL-PROJECTS-008).
 *
 * Controlled: the caller persists the change (typically via `useUpdateIssue`
 * with an optimistic patch that propagates the project badge everywhere).
 */
export function ProjectPicker({
  value,
  onChange,
  projects,
  disabled,
  className,
}: ProjectPickerProps) {
  const current = projects.find((p) => p.id === value)

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
            <Folder className="h-3.5 w-3.5 text-muted-foreground" />
          ) : (
            <Folder className="h-3.5 w-3.5 text-muted-foreground/50" />
          )}
          <span>{current?.name ?? 'No project'}</span>
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="min-w-[16rem]">
        <DropdownMenuLabel>Project</DropdownMenuLabel>
        <DropdownMenuItem onClick={() => onChange(null)} className="gap-2">
          <Ban className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="flex-1">No project</span>
          {value === null && <Check className="h-3.5 w-3.5" />}
        </DropdownMenuItem>
        {projects.length > 0 && <DropdownMenuSeparator />}
        {projects.map((p) => (
          <DropdownMenuItem
            key={p.id}
            onClick={() => onChange(p.id)}
            className="gap-2"
          >
            <Folder className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="flex-1 truncate">{p.name}</span>
            {p.id === value && <Check className="h-3.5 w-3.5" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
