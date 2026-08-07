import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Bookmark, Loader2 } from 'lucide-react'
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
  defaultSaveViewFormValues,
  saveViewFormSchema,
  VIEW_NAME_MAX,
  type SaveViewFormValues,
} from '@/features/views/view-schemas'
import { useCreateView, type CreateViewInput } from '@/hooks/useViews'
import {
  urlSearchToViewConfig,
  hasActiveViewConfig,
} from '@/lib/view-config'
import type { IssueUrlSearch } from '@/lib/issue-search'

interface SaveViewDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  teamId: string
  /** The current Issues/Board view configuration to snapshot into the view. */
  search: IssueUrlSearch
}

/**
 * Save the current view (filters + group_by + sort) as a named View.
 *
 * - Name is required (whitespace-only rejected) — VAL-VIEWS-002.
 * - Captures the current {@link IssueUrlSearch} as the view's filters + sort
 *   (VAL-VIEWS-001). Only displayed when there is an active config worth saving
 *   (the trigger is gated by the caller).
 * - On success the dialog closes and resets; the new view appears in the
 *   sidebar via the optimistic create in {@link useCreateView}.
 */
export function SaveViewDialog({
  open,
  onOpenChange,
  teamId,
  search,
}: SaveViewDialogProps) {
  const createView = useCreateView()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isValid },
  } = useForm({
    resolver: zodResolver(saveViewFormSchema),
    mode: 'onChange',
    defaultValues: defaultSaveViewFormValues(),
  })

  // Reset the name input whenever the dialog opens.
  useEffect(() => {
    if (open) {
      reset(defaultSaveViewFormValues())
    }
  }, [open, reset])

  const onSubmit = handleSubmit(async (values: SaveViewFormValues) => {
    const { filters, group_by, order_by } = urlSearchToViewConfig(search)
    const input: CreateViewInput = {
      team_id: teamId,
      name: values.name,
      filters,
      group_by,
      order_by,
    }
    try {
      await createView.mutateAsync(input)
      onOpenChange(false)
    } catch {
      // Error handled by the hook (toast); keep the dialog open.
    }
  })

  const hasConfig = hasActiveViewConfig(search)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md" showCloseButton>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bookmark className="h-4 w-4" />
            Save view
          </DialogTitle>
          <DialogDescription>
            Save the current filters, grouping, and sort as a view you can return
            to. A name is required.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="view-name" className="sr-only">
              View name
            </label>
            <Input
              id="view-name"
              placeholder="View name"
              maxLength={VIEW_NAME_MAX}
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

          {hasConfig ? (
            <p className="text-xs text-muted-foreground">
              Saves the active filters and sort as <strong>{search.sort ?? 'newest'}</strong>.
            </p>
          ) : (
            <p className="text-xs text-muted-foreground">
              No active filters — this saves the default view configuration.
            </p>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={createView.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!isValid || createView.isPending}>
              {createView.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Saving…
                </>
              ) : (
                'Save view'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
