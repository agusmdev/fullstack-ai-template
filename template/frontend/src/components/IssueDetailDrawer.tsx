import { useEffect, useRef, useState } from 'react'
import { Trash2, Loader2, Folder, Repeat2 } from 'lucide-react'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { StatusPicker } from '@/components/StatusPicker'
import { PriorityPicker } from '@/components/PriorityPicker'
import { AssigneePicker } from '@/components/AssigneePicker'
import { LabelPicker } from '@/components/LabelPicker'
import { ProjectPicker } from '@/components/ProjectPicker'
import { CyclePicker } from '@/components/CyclePicker'
import { StatusDot } from '@/components/StatusDot'
import { SubIssuesPanel } from '@/components/SubIssuesPanel'
import { IssueDetailDrawerSkeleton } from '@/components/IssueDetailDrawerSkeleton'
import {
  useIssue,
  useUpdateIssue,
  useDeleteIssue,
  useAddIssueLabel,
  useRemoveIssueLabel,
} from '@/hooks/useIssues'
import { cn } from '@/lib/utils'
import { ISSUE_TITLE_MAX } from '@/features/issues/issue-schemas'
import type { Issue, IssueLabel } from '@/types/issue'
import type { WorkflowState } from '@/types/workflow-state'
import type { Label } from '@/types/label'
import type { Project } from '@/types/project'
import type { Cycle } from '@/types/cycle'

interface IssueDetailDrawerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  issueId: string | null
  /** The issue already in the list cache, to render instantly without a flash. */
  initialIssue?: Issue
  teamId: string
  /** The team's workflow states, ordered by position. */
  workflowStates: WorkflowState[]
  /** The team's labels. */
  labels: Label[]
  /** The team's projects (for the project picker + badge). */
  projects: Project[]
  /** The team's cycles (for the cycle picker + badge). */
  cycles: Cycle[]
  /** Known assignable members. */
  members: { id: string; name: string }[]
  /** Called when a sub-issue is activated (opens the child's own drawer). */
  onSelectIssue?: (issue: Issue) => void
}

/**
 * Format an ISO timestamp into a short, human-readable date (never `Invalid Date`).
 */
function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Issue detail drawer — a right-side sheet showing every issue field with inline
 * editing.
 *
 * - Opens on row click; shows a skeleton while the issue GET is in flight and
 *   renders complete correct data once loaded (VAL-ISSUES-030, VAL-ISSUES-048).
 * - Inline title (Enter/blur to save) and multiline description editing
 *   (VAL-ISSUES-031, VAL-ISSUES-032).
 * - Status / priority / assignee / label pickers; a status change re-groups the
 *   row and updates counts via the optimistic list cache update
 *   (VAL-ISSUES-033–036, VAL-ISSUES-042/043).
 * - All edits apply optimistically to the drawer + list + counts and roll back
 *   on error (VAL-ISSUES-037, VAL-ISSUES-050, VAL-PERF-002/003).
 * - Delete with a confirm guard; optimistic removal + rollback (VAL-ISSUES-038–040).
 */
export function IssueDetailDrawer({
  open,
  onOpenChange,
  issueId,
  initialIssue,
  teamId,
  workflowStates,
  labels,
  projects,
  cycles,
  members,
  onSelectIssue,
}: IssueDetailDrawerProps) {
  const { data: issue, isLoading } = useIssue(open ? (issueId ?? undefined) : undefined, initialIssue)
  const updateIssue = useUpdateIssue()
  const deleteIssue = useDeleteIssue()
  const addLabel = useAddIssueLabel()
  const removeLabel = useRemoveIssueLabel()

  const [confirmOpen, setConfirmOpen] = useState(false)

  // Inline title editing state.
  const [titleDraft, setTitleDraft] = useState('')
  const [editingTitle, setEditingTitle] = useState(false)
  const titleInputRef = useRef<HTMLInputElement>(null)

  // Inline description editing state.
  const [descDraft, setDescDraft] = useState('')
  const [editingDesc, setEditingDesc] = useState(false)

  // Sync local drafts from the server issue whenever it changes (and not editing).
  useEffect(() => {
    if (issue) {
      setTitleDraft(issue.title)
      setDescDraft(issue.description ?? '')
    }
  }, [issue?.id, issue?.title, issue?.description])

  // Focus the title input when entering edit mode.
  useEffect(() => {
    if (editingTitle) titleInputRef.current?.focus()
  }, [editingTitle])

  const memberNames = new Map(members.map((m) => [m.id, m.name]))
  const currentState = workflowStates.find((s) => s.id === issue?.status_id)
  const isTerminal = currentState?.type === 'completed' || currentState?.type === 'canceled'
  const busy = updateIssue.isPending || addLabel.isPending || removeLabel.isPending

  // --- Title commit -------------------------------------------------------
  const commitTitle = () => {
    if (!issue) return
    setEditingTitle(false)
    const next = titleDraft.trim()
    if (next && next !== issue.title) {
      updateIssue.mutate({ id: issue.id, team_id: teamId, title: next })
    } else {
      setTitleDraft(issue.title)
    }
  }

  // --- Description commit -------------------------------------------------
  const commitDescription = () => {
    if (!issue) return
    setEditingDesc(false)
    const next = descDraft.trim() ? descDraft : null
    if (next !== (issue.description ?? null)) {
      updateIssue.mutate({ id: issue.id, team_id: teamId, description: next })
    } else {
      setDescDraft(issue.description ?? '')
    }
  }

  // --- Picker changes -----------------------------------------------------
  const handleStatusChange = (statusId: string | null) => {
    if (!issue || !statusId || statusId === issue.status_id) return
    updateIssue.mutate({ id: issue.id, team_id: teamId, status_id: statusId })
  }
  const handlePriorityChange = (priority: number) => {
    if (!issue || priority === issue.priority) return
    updateIssue.mutate({ id: issue.id, team_id: teamId, priority })
  }
  const handleAssigneeChange = (assigneeId: string | null) => {
    if (!issue || assigneeId === issue.assignee_id) return
    updateIssue.mutate({ id: issue.id, team_id: teamId, assignee_id: assigneeId })
  }
  const handleLabelsChange = (nextIds: string[]) => {
    if (!issue) return
    const currentIds = issue.labels.map((l) => l.id)
    const addedId = nextIds.find((id) => !currentIds.includes(id))
    const removedId = currentIds.find((id) => !nextIds.includes(id))
    if (addedId) {
      const lbl = labels.find((l) => l.id === addedId)
      if (lbl) {
        const brief: IssueLabel = { id: lbl.id, name: lbl.name, color: lbl.color }
        addLabel.mutate({ id: issue.id, team_id: teamId, label: brief })
      }
    } else if (removedId) {
      const lbl = issue.labels.find((l) => l.id === removedId)
      if (lbl) removeLabel.mutate({ id: issue.id, team_id: teamId, label: lbl })
    }
  }

  const handleProjectChange = (projectId: string | null) => {
    if (!issue || projectId === issue.project_id) return
    updateIssue.mutate({ id: issue.id, team_id: teamId, project_id: projectId })
  }

  const handleCycleChange = (cycleId: string | null) => {
    if (!issue || cycleId === issue.cycle_id) return
    updateIssue.mutate({ id: issue.id, team_id: teamId, cycle_id: cycleId })
  }

  // --- Delete -------------------------------------------------------------
  const handleDelete = () => {
    if (!issue) return
    setConfirmOpen(false)
    deleteIssue.mutate(
      { id: issue.id, team_id: teamId },
      { onSuccess: () => onOpenChange(false) },
    )
  }

  const descriptionBody = issue?.description?.trim()
    ? issue.description
    : null

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent className="w-full sm:max-w-xl" aria-describedby="issue-drawer-desc">
          <SheetDescription id="issue-drawer-desc" className="sr-only">
            Issue details and inline editing.
          </SheetDescription>
          {isLoading || !issue ? (
            <IssueDetailDrawerSkeleton />
          ) : (
            <div className="flex h-full flex-col">
              <SheetHeader className="px-6 pt-6">
                <div className="flex items-center gap-2 pb-1">
                  <StatusDot color={currentState?.color} type={currentState?.type} />
                  <SheetTitle className="font-mono text-sm text-muted-foreground">
                    {issue.identifier || 'Issue'}
                  </SheetTitle>
                </div>
              </SheetHeader>

              <div className="flex-1 overflow-auto px-6 pb-6">
                {/* Title (inline editable) */}
                {editingTitle ? (
                  <Input
                    ref={titleInputRef}
                    value={titleDraft}
                    maxLength={ISSUE_TITLE_MAX}
                    onChange={(e) => setTitleDraft(e.target.value)}
                    onBlur={commitTitle}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        commitTitle()
                      } else if (e.key === 'Escape') {
                        setTitleDraft(issue.title)
                        setEditingTitle(false)
                      }
                    }}
                    className="text-lg font-semibold"
                    aria-label="Issue title"
                  />
                ) : (
                  <h2
                    className={cn(
                      'cursor-text rounded px-1 text-lg font-semibold text-foreground',
                      isTerminal && 'text-muted-foreground line-through',
                    )}
                    onClick={() => setEditingTitle(true)}
                    title="Click to edit title"
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        setEditingTitle(true)
                      }
                    }}
                  >
                    {issue.title}
                  </h2>
                )}

                {/* Description (inline editable, multiline) */}
                <div className="mt-4">
                  {editingDesc ? (
                    <div className="flex flex-col gap-2">
                      <Textarea
                        value={descDraft}
                        rows={6}
                        autoFocus
                        onChange={(e) => setDescDraft(e.target.value)}
                        placeholder="Add a description…"
                        aria-label="Issue description"
                      />
                      <div className="flex gap-2">
                        <Button size="sm" onClick={commitDescription} disabled={updateIssue.isPending}>
                          {updateIssue.isPending ? 'Saving…' : 'Save'}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setDescDraft(issue.description ?? '')
                            setEditingDesc(false)
                          }}
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div
                      className="cursor-text rounded border border-transparent px-1 py-1 text-sm text-foreground hover:border-border"
                      onClick={() => setEditingDesc(true)}
                      title="Click to edit description"
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          setEditingDesc(true)
                        }
                      }}
                    >
                      {descriptionBody ? (
                        <pre
                          data-testid="issue-description"
                          className="whitespace-pre-wrap break-words font-sans"
                        >
                          {descriptionBody}
                        </pre>
                      ) : (
                        <span className="text-muted-foreground">Add a description…</span>
                      )}
                    </div>
                  )}
                </div>

                {/* Property pickers */}
                <div className="mt-6 flex flex-col gap-2">
                  <div className="flex items-center justify-between gap-3 py-1">
                    <span className="w-20 shrink-0 text-xs font-medium text-muted-foreground">Status</span>
                    <StatusPicker
                      value={issue.status_id}
                      onChange={handleStatusChange}
                      states={workflowStates}
                      disabled={busy}
                    />
                  </div>
                  <div className="flex items-center justify-between gap-3 py-1">
                    <span className="w-20 shrink-0 text-xs font-medium text-muted-foreground">Priority</span>
                    <PriorityPicker
                      value={issue.priority}
                      onChange={handlePriorityChange}
                      disabled={busy}
                    />
                  </div>
                  <div className="flex items-center justify-between gap-3 py-1">
                    <span className="w-20 shrink-0 text-xs font-medium text-muted-foreground">Assignee</span>
                    <AssigneePicker
                      value={issue.assignee_id}
                      onChange={handleAssigneeChange}
                      members={members}
                      disabled={busy}
                    />
                  </div>
                  <div className="flex items-center justify-between gap-3 py-1">
                    <span className="w-20 shrink-0 text-xs font-medium text-muted-foreground">Labels</span>
                    <LabelPicker
                      value={issue.labels.map((l) => l.id)}
                      onChange={handleLabelsChange}
                      labels={labels}
                      disabled={busy}
                    />
                  </div>
                  <div className="flex items-center justify-between gap-3 py-1">
                    <span className="w-20 shrink-0 text-xs font-medium text-muted-foreground">Project</span>
                    <ProjectPicker
                      value={issue.project_id}
                      onChange={handleProjectChange}
                      projects={projects}
                      disabled={busy}
                    />
                  </div>
                  <div className="flex items-center justify-between gap-3 py-1">
                    <span className="w-20 shrink-0 text-xs font-medium text-muted-foreground">Cycle</span>
                    <CyclePicker
                      value={issue.cycle_id}
                      onChange={handleCycleChange}
                      cycles={cycles}
                      disabled={busy}
                    />
                  </div>
                </div>

                {/* Project badge (VAL-PROJECTS-009: badge everywhere) */}
                {issue.project_id && (
                  <div className="mt-3 flex flex-wrap gap-1.5 px-1">
                    {(() => {
                      const p = projects.find((pr) => pr.id === issue.project_id)
                      return p ? (
                        <span
                          className="inline-flex items-center gap-1 rounded-full border border-border bg-muted/40 px-2 py-0.5 text-[11px] text-muted-foreground"
                        >
                          <Folder className="h-3 w-3" />
                          {p.name}
                        </span>
                      ) : null
                    })()}
                  </div>
                )}

                {/* Cycle badge (VAL-CYCLES-005: assignment visible everywhere) */}
                {issue.cycle_id && (
                  <div className="mt-1 flex flex-wrap gap-1.5 px-1">
                    {(() => {
                      const c = cycles.find((cy) => cy.id === issue.cycle_id)
                      return c ? (
                        <span
                          className="inline-flex items-center gap-1 rounded-full border border-border bg-muted/40 px-2 py-0.5 text-[11px] text-muted-foreground"
                        >
                          <Repeat2 className="h-3 w-3" />
                          {c.name}
                        </span>
                      ) : null
                    })()}
                  </div>
                )}

                {/* Label badges */}
                {issue.labels.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5 px-1">
                    {issue.labels.map((label) => (
                      <span
                        key={label.id}
                        className="inline-flex items-center gap-1 rounded-full border border-border px-2 py-0.5 text-[11px] text-muted-foreground"
                      >
                        <StatusDot color={label.color} className="h-2 w-2" />
                        {label.name}
                      </span>
                    ))}
                  </div>
                )}

                {/* Sub-issues panel (VAL-SUBISSUES-001/003/005/006) */}
                <SubIssuesPanel
                  issueId={issue.id}
                  teamId={teamId}
                  workflowStates={workflowStates}
                  onSelectIssue={onSelectIssue}
                />

                {/* Metadata */}
                <div className="mt-6 border-t border-border pt-3 text-xs text-muted-foreground">
                  <div className="flex justify-between py-0.5">
                    <span>Created</span>
                    <span>{formatTimestamp(issue.created_at)}</span>
                  </div>
                  <div className="flex justify-between py-0.5">
                    <span>Updated</span>
                    <span>{formatTimestamp(issue.updated_at)}</span>
                  </div>
                  <div className="flex justify-between py-0.5">
                    <span>Creator</span>
                    <span>{issue.creator_id ? (memberNames.get(issue.creator_id) ?? 'You') : '—'}</span>
                  </div>
                </div>
              </div>

              {/* Footer: delete */}
              <div className="flex justify-start border-t border-border px-6 py-3">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                  onClick={() => setConfirmOpen(true)}
                  disabled={deleteIssue.isPending}
                >
                  {deleteIssue.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                  Delete
                </Button>
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>

      {/* Delete confirmation guard (rendered as a sibling to avoid nesting two
          Radix dialog roots) (VAL-ISSUES-039) */}
      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete issue?</AlertDialogTitle>
            <AlertDialogDescription>
              This permanently deletes <span className="font-mono">{issue?.identifier}</span> —
              {' “'}{issue?.title}{'”'}. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteIssue.isPending}
            >
              {deleteIssue.isPending ? 'Deleting…' : 'Delete issue'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
