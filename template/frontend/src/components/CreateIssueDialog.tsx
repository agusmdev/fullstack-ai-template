import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Plus } from 'lucide-react'
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
import { Textarea } from '@/components/ui/textarea'
import { StatusPicker } from '@/components/StatusPicker'
import { PriorityPicker } from '@/components/PriorityPicker'
import { AssigneePicker } from '@/components/AssigneePicker'
import { LabelPicker } from '@/components/LabelPicker'
import {
  createIssueFormSchema,
  defaultCreateIssueFormValues,
  ISSUE_TITLE_MAX,
  PRIORITY_NONE,
} from '@/features/issues/issue-schemas'
import { useCreateIssue } from '@/hooks/useIssues'
import type { CreateIssueInput } from '@/types/issue'
import type { WorkflowState } from '@/types/workflow-state'
import type { Label } from '@/types/label'

interface CreateIssueDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  teamId: string
  /** The team's workflow states, ordered by position. */
  workflowStates: WorkflowState[]
  /** The team's labels. */
  labels: Label[]
  /** Known assignable members (defaults: none → only "Unassigned" offered). */
  members?: { id: string; name: string }[]
}

/**
 * Create-issue dialog.
 *
 * Validation (Zod + react-hook-form):
 *   - Title required, whitespace-only rejected, length ≤ 512 (VAL-ISSUES-002,
 *     VAL-ISSUES-003, VAL-ISSUES-004).
 *   - Description optional, multiline (VAL-ISSUES-007).
 *
 * Defaults on open (VAL-ISSUES-001, VAL-ISSUES-005):
 *   - Status = team's first workflow state (backlog).
 *   - Priority = No priority.
 *   - Assignee = Unassigned.
 *   - Labels = none.
 *
 * On submit the new issue is inserted optimistically before the POST resolves
 * and rolls back on error (see `useCreateIssue`); on success the dialog closes
 * and the form resets to defaults (VAL-ISSUES-009, VAL-ISSUES-010).
 */
export function CreateIssueDialog({
  open,
  onOpenChange,
  teamId,
  workflowStates,
  labels,
  members = [],
}: CreateIssueDialogProps) {
  const createIssue = useCreateIssue()

  const defaultStatusId = workflowStates[0]?.id ?? null

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isValid },
  } = useForm({
    resolver: zodResolver(createIssueFormSchema),
    mode: 'onChange',
    // Pass an object (not a function): RHF treats a function as async/Promise-returning.
    defaultValues: defaultCreateIssueFormValues(),
  })

  // Picker state (controlled; merged into the payload on submit).
  const [statusId, setStatusId] = useState<string | null>(defaultStatusId)
  const [priority, setPriority] = useState<number>(PRIORITY_NONE)
  const [assigneeId, setAssigneeId] = useState<string | null>(null)
  const [labelIds, setLabelIds] = useState<string[]>([])

  // Reset the whole dialog (form + pickers) whenever it opens.
  useEffect(() => {
    if (open) {
      reset(defaultCreateIssueFormValues())
      setStatusId(defaultStatusId)
      setPriority(PRIORITY_NONE)
      setAssigneeId(null)
      setLabelIds([])
    }
  }, [open, defaultStatusId, reset])

  const onSubmit = handleSubmit(async (values) => {
    const input: CreateIssueInput = {
      team_id: teamId,
      title: values.title,
      description: values.description?.trim() ? values.description : null,
      status_id: statusId,
      priority,
      assignee_id: assigneeId,
      label_ids: labelIds.length > 0 ? labelIds : undefined,
      optimisticLabels: labels.filter((l) => labelIds.includes(l.id)),
    }

    try {
      await createIssue.mutateAsync(input)
      // Success: close + reset (the effect on next open re-applies defaults).
      onOpenChange(false)
    } catch {
      // Error: keep the dialog open with input preserved; the hook already
      // rolled back the optimistic row and surfaced a toast (VAL-ISSUES-009).
    }
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl" showCloseButton>
        <DialogHeader>
          <DialogTitle>New issue</DialogTitle>
          <DialogDescription>
            Create a new issue in this team. Title is required.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="issue-title" className="sr-only">
              Title
            </label>
            <Input
              id="issue-title"
              placeholder="Issue title"
              maxLength={ISSUE_TITLE_MAX}
              autoFocus
              aria-invalid={!!errors.title}
              {...register('title')}
            />
            {errors.title && (
              <p className="text-xs text-destructive" role="alert">
                {errors.title.message}
              </p>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="issue-description" className="sr-only">
              Description
            </label>
            <Textarea
              id="issue-description"
              placeholder="Add description…"
              rows={4}
              {...register('description')}
            />
          </div>

          {/* Pickers */}
          <div className="flex flex-wrap items-center gap-2">
            <StatusPicker
              value={statusId}
              onChange={setStatusId}
              states={workflowStates}
              disabled={createIssue.isPending}
            />
            <PriorityPicker
              value={priority}
              onChange={setPriority}
              disabled={createIssue.isPending}
            />
            <AssigneePicker
              value={assigneeId}
              onChange={setAssigneeId}
              members={members}
              disabled={createIssue.isPending}
            />
            <LabelPicker
              value={labelIds}
              onChange={setLabelIds}
              labels={labels}
              disabled={createIssue.isPending}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={createIssue.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!isValid || createIssue.isPending}
            >
              <Plus className="h-4 w-4" />
              {createIssue.isPending ? 'Creating…' : 'Create issue'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
