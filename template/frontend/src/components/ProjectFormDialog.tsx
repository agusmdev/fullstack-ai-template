import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Plus, Check, ChevronDown, Folder } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown'
import { AssigneePicker } from '@/components/AssigneePicker'
import {
  createProjectFormSchema,
  defaultCreateProjectFormValues,
  PROJECT_NAME_MAX,
} from '@/features/projects/project-schemas'
import {
  PROJECT_STATUSES,
  projectStatusOption,
  DEFAULT_PROJECT_STATUS,
} from '@/types/project'
import { useCreateProject, type CreateProjectInput } from '@/hooks/useProjects'
import { cn } from '@/lib/utils'

interface ProjectFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  teamId: string
  /** Known team members for the lead picker. */
  members?: { id: string; name: string }[]
}

/**
 * Create-project dialog.
 *
 * Validation (Zod + react-hook-form):
 *   - Name required, whitespace-only rejected, length ≤ 255 (VAL-PROJECTS-001).
 *
 * Defaults on open (VAL-PROJECTS-002, VAL-PROJECTS-004):
 *   - Status = ``planned`` (non-terminal).
 *   - Lead = Unassigned.
 *   - Target date = empty (optional; formatted when set).
 *
 * On success the dialog closes and the form resets to defaults.
 */
export function ProjectFormDialog({
  open,
  onOpenChange,
  teamId,
  members = [],
}: ProjectFormDialogProps) {
  const createProject = useCreateProject()

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isValid },
  } = useForm({
    resolver: zodResolver(createProjectFormSchema),
    mode: 'onChange',
    defaultValues: defaultCreateProjectFormValues(),
  })

  // Lead is a controlled picker value (always a well-formed UUID or null).
  const [leadId, setLeadId] = useState<string | null>(null)
  // target_date is managed by the form but rendered as a native date input;
  // we sync it back so Zod validates it.
  const targetDateValue = watch('target_date') ?? ''
  const statusValue = watch('status') ?? DEFAULT_PROJECT_STATUS
  const statusOption = projectStatusOption(statusValue)

  // Reset the whole dialog whenever it opens.
  useEffect(() => {
    if (open) {
      reset(defaultCreateProjectFormValues())
      setLeadId(null)
    }
  }, [open, reset])

  const onSubmit = handleSubmit(async (values) => {
    const input: CreateProjectInput = {
      team_id: teamId,
      name: values.name,
      status: values.status,
      lead_id: leadId,
      target_date: values.target_date ? values.target_date : null,
      description: null,
    }
    try {
      await createProject.mutateAsync(input)
      onOpenChange(false)
    } catch {
      // Error handled by the hook (toast); keep the dialog open.
    }
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl" showCloseButton>
        <DialogHeader>
          <DialogTitle>New project</DialogTitle>
          <DialogDescription>
            Group related issues into a project. Name is required.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="project-name" className="sr-only">
              Project name
            </label>
            <Input
              id="project-name"
              placeholder="Project name"
              maxLength={PROJECT_NAME_MAX}
              autoFocus
              aria-invalid={!!errors.name}
              {...register('name')}
            />
            {errors.name && (
              <p className="text-xs text-destructive" role="alert">
                {errors.name.message}
              </p>
            )}
          </div>

          {/* Pickers: status / lead / target date */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Status picker */}
            <DropdownMenu>
              <DropdownMenuTrigger>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={createProject.isPending}
                  className="gap-2 font-normal"
                >
                  <Folder className="h-3.5 w-3.5 text-muted-foreground" />
                  <span>{statusOption.label}</span>
                  <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="min-w-[14rem]">
                {PROJECT_STATUSES.map((s) => (
                  <DropdownMenuItem
                    key={s.value}
                    onClick={() => setValue('status', s.value, { shouldValidate: true })}
                    className="gap-2"
                  >
                    <span
                      className={cn(
                        'h-2 w-2 rounded-full',
                        s.terminal ? 'bg-muted-foreground' : 'bg-primary',
                      )}
                    />
                    <span className="flex-1">{s.label}</span>
                    {s.value === statusValue && <Check className="h-3.5 w-3.5" />}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Lead picker (reuses the member picker) */}
            <AssigneePicker
              value={leadId}
              onChange={setLeadId}
              members={members}
              disabled={createProject.isPending}
            />

            {/* Target date (native date input, optional, formatted) */}
            <div className="flex items-center gap-1.5">
              <input
                type="date"
                aria-label="Target date"
                value={targetDateValue}
                disabled={createProject.isPending}
                onChange={(e) =>
                  setValue('target_date', e.target.value, { shouldValidate: true })
                }
                className="h-8 rounded-md border border-border bg-transparent px-2 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          </div>

          {errors.target_date && (
            <p className="text-xs text-destructive" role="alert">
              {errors.target_date.message}
            </p>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={createProject.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!isValid || createProject.isPending}>
              <Plus className="h-4 w-4" />
              {createProject.isPending ? 'Creating…' : 'Create project'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
