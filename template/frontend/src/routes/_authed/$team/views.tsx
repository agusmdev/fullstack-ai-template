import { createFileRoute } from '@tanstack/react-router'
import { Eye } from 'lucide-react'
import { EmptyState } from '@/components/EmptyState'

/**
 * Views view — saved views (M3). Empty state for M0.
 */
export const Route = createFileRoute('/_authed/$team/views')({
  component: ViewsView,
})

function ViewsView() {
  return (
    <div className="p-6">
      <h1 className="mb-4 text-lg font-semibold text-foreground">Views</h1>
      <EmptyState
        icon={Eye}
        title="No saved views yet"
        description="Save a set of filters, grouping, and sort as a view. Saved views arrive in a later milestone."
      />
    </div>
  )
}
