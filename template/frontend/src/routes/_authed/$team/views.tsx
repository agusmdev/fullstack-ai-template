import { useState } from 'react'
import { createFileRoute, useParams, useNavigate, useRouterState } from '@tanstack/react-router'
import { Eye, Bookmark, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/EmptyState'
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
import { useTeams } from '@/hooks/useTeams'
import { useViews, useDeleteView } from '@/hooks/useViews'
import { Skeleton } from '@/components/ui/skeleton'
import { validateIssueSearch } from '@/lib/issue-search'
import { viewMatchesSearch, viewToUrlSearch } from '@/lib/view-config'
import { cn } from '@/lib/utils'
import type { View } from '@/types/view'

/**
 * Views page — manage saved views for the active team.
 *
 * Lists each saved view with its name + a summary of its captured config. A
 * saved view can be applied (navigate to Issues/Board with its config), or
 * deleted. A clean empty state shows when the team has no saved views
 * (VAL-VIEWS-005, VAL-CROSS-003). New views are saved from the Issues/Board
 * header's "Save view" action (which snapshots the current config).
 */
export const Route = createFileRoute('/_authed/$team/views')({
  component: ViewsView,
})

function ViewsView() {
  const { team: teamKey } = useParams({ strict: false })
  const navigate = useNavigate()

  const { data: teamsData, isLoading: teamsLoading } = useTeams()
  const teamObj = (teamsData?.items ?? []).find((t) => t.key === teamKey)
  const teamId = teamObj?.id

  const { data, isLoading } = useViews(teamId)
  const views = data?.items ?? []

  const deleteView = useDeleteView()
  const [pendingDelete, setPendingDelete] = useState<View | null>(null)

  // Active-view highlight + apply (mirrors the sidebar SavedViews logic).
  const locationSearch = useRouterState({
    select: (s) => s.location.search,
  }) as Record<string, unknown>
  const currentSearch = validateIssueSearch(locationSearch)
  const pathname = useRouterState({ select: (s) => s.location.pathname })

  const applyView = (view: View) => {
    const search = viewToUrlSearch(view)
    const to = pathname.endsWith('/board') ? '/$team/board' : '/$team/issues'
    void navigate({ to, params: { team: teamKey ?? '' }, search })
  }

  const confirmDelete = () => {
    if (pendingDelete && teamId) {
      deleteView.mutate({ id: pendingDelete.id, team_id: teamId })
    }
    setPendingDelete(null)
  }

  const initialLoading = teamsLoading || isLoading

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-6 py-3">
        <h1 className="text-base font-semibold text-foreground">Views</h1>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-auto p-6">
        {initialLoading ? (
          <div className="flex flex-col gap-2">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : views.length === 0 ? (
          <EmptyState
            icon={Eye}
            title="No saved views yet"
            description="Open Issues or the Board, set your filters and sort, then choose “Save view” to keep a view you can return to anytime."
          />
        ) : (
          <ul className="flex flex-col gap-2">
            {views.map((view) => {
              const active = viewMatchesSearch(view, currentSearch)
              return (
                <li
                  key={view.id}
                  className={cn(
                    'flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3 transition-colors',
                    active && 'ring-1 ring-primary/40',
                  )}
                >
                  <button
                    type="button"
                    onClick={() => applyView(view)}
                    className="flex min-w-0 flex-1 items-center gap-3 text-left"
                  >
                    <Bookmark className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-foreground">
                        {view.name}
                      </p>
                      <p className="truncate text-xs text-muted-foreground">
                        Sort: {view.order_by ?? 'newest'}
                        {view.group_by ? ` · Group by ${view.group_by}` : ''}
                        {Object.keys(view.filters ?? {}).length > 0
                          ? ` · ${Object.keys(view.filters).length} filter${
                              Object.keys(view.filters).length === 1 ? '' : 's'
                            }`
                          : ' · No filters'}
                      </p>
                    </div>
                  </button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setPendingDelete(view)}
                    aria-label={`Delete view “${view.name}”`}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </li>
              )
            })}
          </ul>
        )}
      </div>

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
