import { useState } from 'react'
import { Plus, X, Loader2, ChevronDown, ChevronRight } from 'lucide-react'
import { PriorityIcon } from '@/components/PriorityIcon'
import { StatusDot } from '@/components/StatusDot'
import { cn } from '@/lib/utils'
import {
  useIssueDependencies,
  useCreateIssueDependency,
  useDeleteIssueDependency,
  useTeamIssuesForPicker,
  splitDependencies,
} from '@/hooks/useIssueDependencies'
import type { Issue } from '@/types/issue'
import type { DependencyIssueBrief, IssueDependency } from '@/types/issue-dependency'
import type { WorkflowState } from '@/types/workflow-state'

interface DependenciesPanelProps {
  /** The issue whose dependencies to display. */
  issueId: string
  teamId: string
  /** The team's workflow states, ordered by position (for status dots). */
  workflowStates: WorkflowState[]
  /** Called when a related issue is activated to open its own drawer. */
  onSelectIssue?: (issue: Issue) => void
}

/**
 * Dependencies panel — shown in the issue detail drawer.
 *
 * Reciprocal display (VAL-DEPS-002 / VAL-CROSS-013):
 *  - **Blocking**: issues this issue blocks ("this issue blocks X").
 *  - **Blocked by**: issues blocking this one ("blocked by X").
 *
 * Both lists derive from the same dependency records (the backend returns every
 * dependency involving the issue via ``?issue_id=``). Adding a link from either
 * side persists an ``IssueDependency``; deleting the × removes it from both
 * issues (VAL-DEPS-004). The picker offers only same-team issues (VAL-DEPS-005).
 * A cycle-forming link is rejected by the backend (409) and surfaced as a clear
 * error toast (VAL-DEPS-003).
 */
export function DependenciesPanel({
  issueId,
  teamId,
  workflowStates,
  onSelectIssue,
}: DependenciesPanelProps) {
  const depsQuery = useIssueDependencies(issueId, teamId)
  const createDep = useCreateIssueDependency()
  const deleteDep = useDeleteIssueDependency()
  const [expanded, setExpanded] = useState(true)

  const deps = depsQuery.data?.items ?? []
  const { blocking, blockedBy } = splitDependencies(deps, issueId)
  const total = deps.length
  const busy = createDep.isPending || deleteDep.isPending

  return (
    <div className="mt-4 border-t border-border pt-4">
      {/* Header: expand/collapse + count */}
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
          Dependencies
        </span>
        <span className="text-xs text-muted-foreground/70">{total}</span>
      </button>

      {expanded && (
        <div className="mt-2 flex flex-col gap-3">
          {depsQuery.isLoading ? (
            <div className="flex items-center gap-1.5 px-1 py-1 text-xs text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              Loading…
            </div>
          ) : (
            <>
              {/* Blocking: issues this issue blocks */}
              <DependencySection
                title="Blocking"
                emptyText="Not blocking any issues"
                deps={blocking}
                resolveOther={(d) => d.blocked}
                issueId={issueId}
                workflowStates={workflowStates}
                onSelectIssue={onSelectIssue}
                onDelete={(id) => deleteDep.mutate({ id, team_id: teamId })}
                busy={busy}
              />
              {blocking.length === 0 && (
                <AddDependency
                  direction="blocking"
                  issueId={issueId}
                  teamId={teamId}
                  existing={deps}
                  onAdd={(otherId) =>
                    createDep.mutate({
                      blocker_id: issueId,
                      blocked_id: otherId,
                      team_id: teamId,
                    })
                  }
                  busy={busy}
                />
              )}

              {/* Blocked by: issues blocking this one */}
              <DependencySection
                title="Blocked by"
                emptyText="Not blocked by any issues"
                deps={blockedBy}
                resolveOther={(d) => d.blocker}
                issueId={issueId}
                workflowStates={workflowStates}
                onSelectIssue={onSelectIssue}
                onDelete={(id) => deleteDep.mutate({ id, team_id: teamId })}
                busy={busy}
              />
              {blockedBy.length === 0 && (
                <AddDependency
                  direction="blockedBy"
                  issueId={issueId}
                  teamId={teamId}
                  existing={deps}
                  onAdd={(otherId) =>
                    createDep.mutate({
                      blocker_id: otherId,
                      blocked_id: issueId,
                      team_id: teamId,
                    })
                  }
                  busy={busy}
                />
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

/** A single reciprocal section (Blocking or Blocked by). */
function DependencySection({
  title,
  emptyText,
  deps,
  resolveOther,
  workflowStates,
  onSelectIssue,
  onDelete,
  busy,
}: {
  title: string
  emptyText: string
  deps: IssueDependency[]
  resolveOther: (d: IssueDependency) => DependencyIssueBrief
  issueId: string
  workflowStates: WorkflowState[]
  onSelectIssue?: (issue: Issue) => void
  onDelete: (id: string) => void
  busy: boolean
}) {
  return (
    <div>
      <div className="px-1 pb-0.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground/70">
        {title}
      </div>
      {deps.length === 0 ? (
        <p className="px-1 py-0.5 text-xs text-muted-foreground/60">{emptyText}</p>
      ) : (
        deps.map((dep) => {
          const other = resolveOther(dep)
          const state = workflowStates.find((s) => s.id === other.status_id)
          const isTerminal =
            state?.type === 'completed' || state?.type === 'canceled'
          return (
            <div
              key={dep.id}
              className="group flex items-center gap-2 rounded-md border border-border bg-card px-2 py-1.5 transition-colors hover:bg-accent/40"
            >
              <StatusDot
                color={state?.color}
                type={state?.type}
                className="h-2 w-2 shrink-0"
              />
              <PriorityIcon priority={other.priority} />
              <span className="w-14 shrink-0 font-mono text-[11px] text-muted-foreground">
                {other.identifier || '···'}
              </span>
              <button
                type="button"
                className={cn(
                  'min-w-0 flex-1 truncate text-left text-xs text-foreground',
                  onSelectIssue && 'cursor-pointer hover:text-primary',
                  isTerminal && 'text-muted-foreground line-through',
                )}
                onClick={() =>
                  onSelectIssue?.(briefToIssue(other))
                }
                title={other.title}
              >
                {other.title}
              </button>
              <button
                type="button"
                className="shrink-0 rounded p-0.5 text-muted-foreground opacity-0 transition-opacity hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100"
                onClick={() => onDelete(dep.id)}
                title="Remove dependency"
                disabled={busy}
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          )
        })
      )}
    </div>
  )
}

/** Cast a dependency brief into the Issue subset needed by onSelectIssue. */
function briefToIssue(brief: DependencyIssueBrief): Issue {
  return {
    id: brief.id,
    team_id: '',
    identifier: brief.identifier,
    title: brief.title,
    description: null,
    status_id: brief.status_id,
    priority: brief.priority,
    assignee_id: null,
    creator_id: '',
    project_id: null,
    cycle_id: null,
    parent_id: null,
    sort_order: 0,
    estimate: null,
    due_date: null,
    labels: [],
    created_at: '',
    updated_at: '',
  }
}

/**
 * Inline picker to add a dependency. Offers only same-team issues (the backend
 * scopes the picker query by ``team_id`` — VAL-DEPS-005), excluding the current
 * issue and issues already linked to it. A cycle-forming pick is rejected by
 * the backend (409) and surfaced as a clear error toast (VAL-DEPS-003).
 *
 * Renders candidates as a list of buttons rather than a native ``<select>``:
 * native selects conflict with the Radix modal Sheet's focus handling (the
 * sheet closes when the select mounts).
 */
function AddDependency({
  direction,
  issueId,
  teamId,
  existing,
  onAdd,
  busy,
}: {
  direction: 'blocking' | 'blockedBy'
  issueId: string
  teamId: string
  existing: IssueDependency[]
  onAdd: (otherId: string) => void
  busy: boolean
}) {
  const [open, setOpen] = useState(false)
  const { data, isLoading } = useTeamIssuesForPicker(teamId, open)

  const label = direction === 'blocking' ? 'Add blocking' : 'Add blocked by'

  if (!open) {
    return (
      <button
        type="button"
        className="flex items-center gap-1 px-1 text-xs text-muted-foreground hover:text-foreground"
        onClick={() => setOpen(true)}
      >
        <Plus className="h-3 w-3" />
        {label}
      </button>
    )
  }

  // Exclude the current issue and any issue already linked (either side) so the
  // picker can't offer a duplicate or a self-link.
  const linkedIds = new Set([
    issueId,
    ...existing.flatMap((d) => [d.blocker_id, d.blocked_id]),
  ])
  const candidates = (data?.items ?? []).filter((i) => !linkedIds.has(i.id))

  return (
    <div className="flex flex-col gap-1 rounded-md border border-border bg-card px-2 py-1.5">
      <div className="max-h-40 overflow-auto">
        {isLoading ? (
          <span className="px-1 py-0.5 text-xs text-muted-foreground">
            Loading…
          </span>
        ) : candidates.length === 0 ? (
          <span className="px-1 py-0.5 text-xs text-muted-foreground/60">
            No issues available
          </span>
        ) : (
          candidates.map((i) => (
            <button
              key={i.id}
              type="button"
              disabled={busy}
              className="flex w-full items-center gap-2 rounded px-1 py-1 text-left text-xs text-foreground hover:bg-accent/60 disabled:opacity-50"
              onClick={() => {
                onAdd(i.id)
                setOpen(false)
              }}
            >
              <PriorityIcon priority={i.priority} />
              <span className="w-14 shrink-0 font-mono text-[11px] text-muted-foreground">
                {i.identifier}
              </span>
              <span className="min-w-0 flex-1 truncate">{i.title}</span>
            </button>
          ))
        )}
      </div>
      <button
        type="button"
        className="self-start text-xs text-muted-foreground hover:text-foreground"
        onClick={() => setOpen(false)}
      >
        Cancel
      </button>
    </div>
  )
}
