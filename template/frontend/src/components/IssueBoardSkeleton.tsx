import { Skeleton } from '@/components/ui/skeleton'

/**
 * Loading skeleton for the kanban board. Renders placeholder columns with
 * ghost cards so the initial fetch shows a structured loading state, not a
 * flash of the empty state (VAL-ISSUES-047, VAL-PERF-001).
 */
export function IssueBoardSkeleton({ columns = 4 }: { columns?: number }) {
  return (
    <div
      className="flex h-full gap-3 overflow-hidden"
      role="status"
      aria-busy="true"
    >
      {Array.from({ length: columns }).map((_, c) => (
        <div key={c} className="flex w-72 shrink-0 flex-col rounded-lg bg-muted/40">
          <div className="flex items-center gap-2 px-3 py-2.5">
            <Skeleton className="h-3.5 w-3.5 rounded-full" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-3.5 w-4 rounded-full" />
          </div>
          <div className="flex flex-col gap-2 px-2 pb-2">
            {Array.from({ length: 2 }).map((_, r) => (
              <div
                key={r}
                className="flex flex-col gap-1.5 rounded-lg border border-border p-3"
              >
                <Skeleton className="h-4 w-full" />
                <div className="flex items-center gap-2">
                  <Skeleton className="h-3.5 w-3.5 rounded-full" />
                  <Skeleton className="h-3 w-12" />
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
      <span className="sr-only">Loading board…</span>
    </div>
  )
}
