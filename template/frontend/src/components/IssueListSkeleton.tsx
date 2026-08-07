import { Skeleton } from '@/components/ui/skeleton'

/**
 * Loading skeleton for the grouped issues list. Renders placeholder group
 * headers + rows so the initial fetch shows a structured loading state, not a
 * flash of the empty state (VAL-ISSUES-047, VAL-PERF-001).
 */
export function IssueListSkeleton({ groups = 3 }: { groups?: number }) {
  return (
    <div className="flex flex-col gap-4" role="status" aria-busy="true">
      {Array.from({ length: groups }).map((_, g) => (
        <div key={g} className="flex flex-col gap-1">
          <div className="mb-1.5 flex items-center gap-2 px-1">
            <Skeleton className="h-3.5 w-3.5 rounded-full" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-3.5 w-4 rounded-full" />
          </div>
          {Array.from({ length: 2 }).map((_, r) => (
            <div
              key={r}
              className="flex items-center gap-3 rounded-md border border-border px-3 py-2"
            >
              <Skeleton className="h-3.5 w-3.5 rounded-full" />
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 flex-1" />
              <Skeleton className="h-6 w-6 rounded-full" />
            </div>
          ))}
        </div>
      ))}
      <span className="sr-only">Loading issues…</span>
    </div>
  )
}
