import { useState } from 'react'
import { useNavigate, useRouterState } from '@tanstack/react-router'
import { Bookmark, Trash2, Eye } from 'lucide-react'
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
import { Skeleton } from '@/components/ui/skeleton'
import { useViews, useDeleteView } from '@/hooks/useViews'
import { validateIssueSearch } from '@/lib/issue-search'
import { viewMatchesSearch, viewToUrlSearch } from '@/lib/view-config'
import { cn } from '@/lib/utils'
import type { View } from '@/types/view'

interface SavedViewsProps {
  /** The active team key (URL segment) for navigation. */
  teamKey: string | undefined
  /** The active team UUID (for the views query). */
  teamId: string | undefined
}

/**
 * Saved-views section for the workspace sidebar.
 *
 * - Lists the active team's saved views (polling keeps it fresh).
 * - Clicking a view applies its full configuration (filters + group_by + sort)
 *   by navigating to the current Issues/Board route with the stored search
 *   params (VAL-VIEWS-003).
 * - The view whose stored config matches the current URL search is highlighted
 *   as active; once the user changes a filter the match breaks (dirty) and the
 *   highlight drops — the stored view is never overwritten unless explicitly
 *   re-saved (VAL-VIEWS-006).
 * - Each view has a delete control (confirm guard) that removes it
 *   optimistically (VAL-VIEWS-004).
 * - Shows a clean empty state when the team has no saved views (VAL-VIEWS-005).
 */
export function SavedViews({ teamKey, teamId }: SavedViewsProps) {
  const { data, isLoading } = useViews(teamId)
  const views = data?.items ?? []

  // Derive the current URL search (validated to the Issues/Board shape) so we
  // can highlight the active view and detect dirty state. Reading from the
  // router location (non-strict) works regardless of which route is mounted.
  const locationSearch = useRouterState({
    select: (s) => s.location.search,
  }) as Record<string, unknown>
  const currentSearch = validateIssueSearch(locationSearch)
  const pathname = useRouterState({ select: (s) => s.location.pathname })

  const navigate = useNavigate()
  const deleteView = useDeleteView()
  const [pendingDelete, setPendingDelete] = useState<View | null>(null)

  /** Apply a saved view: navigate to the Issues/Board route with its config. */
  const applyView = (view: View) => {
    const search = viewToUrlSearch(view)
    // Stay on the Board if that's where the user is; otherwise go to Issues.
    const to = pathname.endsWith('/board') ? '/$team/board' : '/$team/issues'
    void navigate({
      to,
      params: { team: teamKey ?? '' },
      search,
    })
  }

  const confirmDelete = () => {
    if (pendingDelete && teamId) {
      deleteView.mutate({ id: pendingDelete.id, team_id: teamId })
    }
    setPendingDelete(null)
  }

  return (
    <div className="mt-2 flex-1 border-t border-border px-2 py-3">
      <p className="px-2 pb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground/70">
        Views
      </p>

      {isLoading ? (
        <div className="flex flex-col gap-1 px-2 py-1">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-5 w-24" />
        </div>
      ) : views.length === 0 ? (
        /* Empty state (VAL-VIEWS-005). */
        <div className="flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm text-muted-foreground/60">
          <Bookmark className="h-4 w-4" />
          No saved views
        </div>
      ) : (
        <ul className="flex flex-col gap-0.5" aria-label="Saved views">
          {views.map((view) => {
            const active = viewMatchesSearch(view, currentSearch)
            return (
              <li key={view.id} className="group relative">
                <button
                  type="button"
                  onClick={() => applyView(view)}
                  aria-current={active ? 'true' : undefined}
                  title={active ? 'Active view' : `Apply “${view.name}”`}
                  className={cn(
                    'flex w-full items-center gap-2.5 rounded-md px-2 py-1.5 text-left text-sm font-medium no-underline transition-colors',
                    active
                      ? 'bg-accent text-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-foreground',
                  )}
                >
                  <Eye className="h-4 w-4 shrink-0" />
                  <span className="min-w-0 flex-1 truncate">{view.name}</span>
                  {active && (
                    <span
                      className="h-1.5 w-1.5 shrink-0 rounded-full bg-primary"
                      aria-hidden
                    />
                  )}
                </button>
                {/* Delete control (confirm guard) — VAL-VIEWS-004. */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    setPendingDelete(view)
                  }}
                  aria-label={`Delete view “${view.name}”`}
                  title="Delete view"
                  className="absolute right-1 top-1/2 hidden -translate-y-1/2 rounded p-1 text-muted-foreground opacity-0 transition-opacity hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100 group-focus-within:opacity-100 data-[state=open]:opacity-100"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </li>
            )
          })}
        </ul>
      )}

      {/* Delete confirmation */}
      <AlertDialog
        open={!!pendingDelete}
        onOpenChange={(open) => !open && setPendingDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete view?</AlertDialogTitle>
            <AlertDialogDescription>
              {pendingDelete
                ? `“${pendingDelete.name}” will be permanently removed. This won't affect your issues.`
                : ''}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
