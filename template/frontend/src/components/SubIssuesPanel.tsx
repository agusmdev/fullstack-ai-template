import { useState } from 'react'
import { Plus, X, Loader2, ChevronDown, ChevronRight, Link2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { PriorityIcon } from '@/components/PriorityIcon'
import { StatusDot } from '@/components/StatusDot'
import { cn } from '@/lib/utils'
import {
  useSubIssues,
  useCreateIssue,
  useUpdateIssue,
  useTopLevelIssues,
} from '@/hooks/useIssues'
import type { Issue } from '@/types/issue'
import type { WorkflowState } from '@/types/workflow-state'

interface SubIssuesPanelProps {
  /** The parent issue whose sub-issues to display. */
  issueId: string
  teamId: string
  /** The team's workflow states, ordered by position. */
  workflowStates: WorkflowState[]
  /** Called when a sub-issue row is activated to open its own drawer. */
  onSelectIssue?: (issue: Issue) => void
}

/**
 * Compute aggregate progress over a set of child issues.
 *
 * Returns the total count and how many are in a terminal status
 * (completed/canceled), matching the workflow states' types.
 */
export function computeSubIssueProgress(
  children: Issue[],
  workflowStates: WorkflowState[],
): { total: number; done: number } {
  const terminalStatusIds = new Set(
    workflowStates
      .filter((s) => s.type === 'completed' || s.type === 'canceled')
      .map((s) => s.id),
  )
  const done = children.filter((c) => terminalStatusIds.has(c.status_id)).length
  return { total: children.length, done }
}

/**
 * Sub-issues panel — shown in the issue detail drawer.
 *
 * - Lists the parent's children (sub-issues) with their identifier, title,
 *   priority, and status dot (VAL-SUBISSUES-001, VAL-SUBISSUES-003).
 * - Shows an aggregate progress indicator ("X of Y" + bar) derived from the
 *   children's statuses (VAL-SUBISSUES-006).
 * - Each sub-issue is clickable to open its own drawer (fully editable)
 *   (VAL-SUBISSUES-003).
 * - Add a new sub-issue via an inline title input (creates a child with
 *   ``parent_id`` set).
 * - Remove the parent-child link via an "×" on each row (PATCH ``parent_id``
 *   = null); the child detaches but remains a valid top-level issue
 *   (VAL-SUBISSUES-005).
 */
export function SubIssuesPanel({
  issueId,
  teamId,
  workflowStates,
  onSelectIssue,
}: SubIssuesPanelProps) {
  const subIssuesQuery = useSubIssues(issueId, teamId)
  const createIssue = useCreateIssue()
  const updateIssue = useUpdateIssue()
  const [expanded, setExpanded] = useState(true)
  const [adding, setAdding] = useState(false)
  const [titleDraft, setTitleDraft] = useState('')

  const children = subIssuesQuery.data?.items ?? []
  const { total, done } = computeSubIssueProgress(children, workflowStates)
  const pct = total > 0 ? Math.round((done / total) * 100) : 0

  const handleAdd = async () => {
    const title = titleDraft.trim()
    if (!title) return
    setTitleDraft('')
    try {
      await createIssue.mutateAsync({
        team_id: teamId,
        title,
        status_id: null,
        priority: 4,
        parent_id: issueId,
      })
    } catch {
      // Error toast handled by the hook.
    }
  }

  const handleDetach = (childId: string) => {
    updateIssue.mutate({ id: childId, team_id: teamId, parent_id: null })
  }

  const handleLink = (childId: string) => {
    updateIssue.mutate({ id: childId, team_id: teamId, parent_id: issueId })
  }

  const busy = createIssue.isPending || updateIssue.isPending

  return (
    <div className="mt-6 border-t border-border pt-4">
      {/* Header: expand/collapse + count + progress */}
      <button
        type="button"
        className="flex w-full items-center gap-1.5 text-left"
        onClick={() => setExpanded((v) => !v)}
      >
        {expanded ? (
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
        )}
        <span className="text-xs font-medium text-muted-foreground">
          Sub-issues
        </span>
        <span className="text-xs text-muted-foreground/70">
          {total > 0 ? `${done}/${total}` : total}
        </span>
        {/* Progress bar */}
        {total > 0 && (
          <div className="ml-2 h-1.5 w-20 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary/60 transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>
        )}
      </button>

      {expanded && (
        <div className="mt-2 flex flex-col gap-1">
          {subIssuesQuery.isLoading ? (
            <div className="flex items-center gap-1.5 px-1 py-1 text-xs text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              Loading…
            </div>
          ) : children.length === 0 && !adding ? (
            <p className="px-1 py-1 text-xs text-muted-foreground/60">
              No sub-issues
            </p>
          ) : (
            children.map((child) => {
              const childState = workflowStates.find((s) => s.id === child.status_id)
              const isTerminal =
                childState?.type === 'completed' || childState?.type === 'canceled'
              return (
                <div
                  key={child.id}
                  className="group flex items-center gap-2 rounded-md border border-border bg-card px-2 py-1.5 transition-colors hover:bg-accent/40"
                >
                  <StatusDot color={childState?.color} type={childState?.type} className="h-2 w-2 shrink-0" />
                  <PriorityIcon priority={child.priority} />
                  <span className="w-14 shrink-0 font-mono text-[11px] text-muted-foreground">
                    {child.identifier || '···'}
                  </span>
                  <button
                    type="button"
                    className={cn(
                      'min-w-0 flex-1 truncate text-left text-xs text-foreground',
                      onSelectIssue && 'cursor-pointer hover:text-primary',
                      isTerminal && 'text-muted-foreground line-through',
                    )}
                    onClick={() => onSelectIssue?.(child)}
                    title={child.title}
                  >
                    {child.title}
                  </button>
                  {/* Detach button (remove parent link — VAL-SUBISSUES-005) */}
                  <button
                    type="button"
                    className="shrink-0 rounded p-0.5 text-muted-foreground opacity-0 transition-opacity hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100"
                    onClick={() => handleDetach(child.id)}
                    title="Remove from parent"
                    disabled={busy}
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              )
            })
          )}

          {/* Inline add-sub-issue input */}
          {adding ? (
            <div className="flex items-center gap-2 pt-1">
              <Input
                value={titleDraft}
                autoFocus
                placeholder="Sub-issue title"
                maxLength={512}
                className="h-8 text-xs"
                onChange={(e) => setTitleDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    void handleAdd()
                  } else if (e.key === 'Escape') {
                    setTitleDraft('')
                    setAdding(false)
                  }
                }}
              />
              <Button
                size="sm"
                variant="ghost"
                className="h-8 px-2"
                onClick={() => {
                  setTitleDraft('')
                  setAdding(false)
                }}
                disabled={busy}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                className="h-8"
                onClick={handleAdd}
                disabled={!titleDraft.trim() || busy}
              >
                {busy ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
                Add
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-3 pt-0.5">
              <button
                type="button"
                className="flex items-center gap-1 px-1 py-1 text-xs text-muted-foreground hover:text-foreground"
                onClick={() => setAdding(true)}
              >
                <Plus className="h-3 w-3" />
                Add sub-issue
              </button>
              <LinkExistingSubIssue issueId={issueId} teamId={teamId} onLink={handleLink} busy={busy} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * Inline picker to **link an existing top-level issue** as a sub-issue.
 *
 * Fetches the team's top-level issues (parent_id IS NULL) and offers them in a
 * native ``<select>``. Selecting one PATCHes its ``parent_id`` to the current
 * parent (VAL-SUBISSUES-001 — "link existing"). The current parent and issues
 * already shown as children are excluded from the candidates.
 */
function LinkExistingSubIssue({
  issueId,
  teamId,
  onLink,
  busy,
}: {
  issueId: string
  teamId: string
  onLink: (childId: string) => void
  busy: boolean
}) {
  const [open, setOpen] = useState(false)
  const { data } = useTopLevelIssues(teamId, open)

  if (!open) {
    return (
      <button
        type="button"
        className="flex items-center gap-1 px-1 py-1 text-xs text-muted-foreground hover:text-foreground"
        onClick={() => setOpen(true)}
      >
        <Link2 className="h-3 w-3" />
        Link existing
      </button>
    )
  }

  const candidates = (data?.items ?? []).filter(
    (i) => i.id !== issueId,
  )

  return (
    <div className="flex items-center gap-2">
      <select
        className="h-8 rounded-md border border-border bg-card px-2 text-xs text-foreground"
        defaultValue=""
        autoFocus
        onChange={(e) => {
          const val = e.target.value
          if (val) onLink(val)
          setOpen(false)
        }}
        disabled={busy}
        aria-label="Link existing issue as sub-issue"
      >
        <option value="" disabled>
          {data ? (candidates.length > 0 ? 'Select an issue…' : 'No top-level issues') : 'Loading…'}
        </option>
        {candidates.map((i) => (
          <option key={i.id} value={i.id}>
            {i.identifier} — {i.title}
          </option>
        ))}
      </select>
      <button
        type="button"
        className="text-xs text-muted-foreground hover:text-foreground"
        onClick={() => setOpen(false)}
      >
        Cancel
      </button>
    </div>
  )
}
