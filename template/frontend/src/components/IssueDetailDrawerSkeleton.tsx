import { Skeleton } from '@/components/ui/skeleton'

/**
 * Loading skeleton for the issue detail drawer. Renders a structured layout
 * (identifier, title, description, property rows) so opening the drawer while
 * the issue GET is in flight shows a placeholder, not a flash of empty content
 * (VAL-ISSUES-048, VAL-PERF-001).
 */
export function IssueDetailDrawerSkeleton() {
  return (
    <div className="flex flex-col gap-5 px-6 py-6" role="status" aria-busy="true">
      <div className="flex items-center gap-2">
        <Skeleton className="h-4 w-20" />
      </div>
      <Skeleton className="h-7 w-3/4" />
      <div className="flex flex-col gap-2">
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-20 w-full" />
      </div>
      <div className="flex flex-col gap-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex items-center justify-between">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-7 w-32" />
          </div>
        ))}
      </div>
      <span className="sr-only">Loading issue…</span>
    </div>
  )
}
