import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Plus, Repeat2 } from 'lucide-react'
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
  createCycleFormSchema,
  defaultCreateCycleFormValues,
  CYCLE_NAME_MAX,
} from '@/features/cycles/cycle-schemas'
import { useCreateCycle, type CreateCycleInput } from '@/hooks/useCycles'

interface CycleFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  teamId: string
}

/**
 * Create-cycle dialog.
 *
 * Validation (Zod + react-hook-form):
 *   - Name required, whitespace-only rejected, length ≤ 255 (VAL-CYCLES-001).
 *   - Start date and end date required (VAL-CYCLES-001).
 *   - End date must be after start date (VAL-CYCLES-002).
 *
 * On success the dialog closes and the form resets to defaults.
 */
export function CycleFormDialog({
  open,
  onOpenChange,
  teamId,
}: CycleFormDialogProps) {
  const createCycle = useCreateCycle()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isValid },
  } = useForm({
    resolver: zodResolver(createCycleFormSchema),
    mode: 'onChange',
    defaultValues: defaultCreateCycleFormValues(),
  })

  // Reset the whole dialog whenever it opens.
  useEffect(() => {
    if (open) {
      reset(defaultCreateCycleFormValues())
    }
  }, [open, reset])

  const onSubmit = handleSubmit(async (values) => {
    const input: CreateCycleInput = {
      team_id: teamId,
      name: values.name,
      starts_at: values.starts_at,
      ends_at: values.ends_at,
    }
    try {
      await createCycle.mutateAsync(input)
      onOpenChange(false)
    } catch {
      // Error handled by the hook (toast); keep the dialog open.
    }
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl" showCloseButton>
        <DialogHeader>
          <DialogTitle>New cycle</DialogTitle>
          <DialogDescription>
            Create a time-boxed sprint. Name, start date, and end date are required.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="cycle-name" className="sr-only">
              Cycle name
            </label>
            <Input
              id="cycle-name"
              placeholder="Cycle name"
              maxLength={CYCLE_NAME_MAX}
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

          {/* Date window pickers */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="cycle-start" className="text-xs text-muted-foreground">
                Start date
              </label>
              <input
                type="date"
                id="cycle-start"
                aria-label="Start date"
                disabled={createCycle.isPending}
                {...register('starts_at')}
                className="h-9 rounded-md border border-border bg-transparent px-2 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring"
              />
              {errors.starts_at && (
                <p className="text-xs text-destructive" role="alert">
                  {errors.starts_at.message}
                </p>
              )}
            </div>

            <Repeat2 className="mt-5 h-4 w-4 text-muted-foreground" />

            <div className="flex flex-col gap-1.5">
              <label htmlFor="cycle-end" className="text-xs text-muted-foreground">
                End date
              </label>
              <input
                type="date"
                id="cycle-end"
                aria-label="End date"
                disabled={createCycle.isPending}
                {...register('ends_at')}
                className="h-9 rounded-md border border-border bg-transparent px-2 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring"
              />
              {errors.ends_at && (
                <p className="text-xs text-destructive" role="alert">
                  {errors.ends_at.message}
                </p>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={createCycle.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!isValid || createCycle.isPending}>
              <Plus className="h-4 w-4" />
              {createCycle.isPending ? 'Creating…' : 'Create cycle'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
