import { createFileRoute } from '@tanstack/react-router'
import { Inbox } from 'lucide-react'
import { EmptyState } from '@/components/EmptyState'

/**
 * Issues view — team-scoped list of issues.
 *
 * The grouped issues list, filters, and create-issue flow arrive in M1. For M0
 * this renders an intentional empty state (no issues yet) so the surface is
 * never a blank screen or a spinner, and the sidebar Issues entry has a target.
 */
export const Route = createFileRoute('/_authed/$team/issues')({
  component: IssuesView,
})

function IssuesView() {
  return (
    <div className="p-6">
      <h1 className="mb-4 text-lg font-semibold text-foreground">Issues</h1>
      <EmptyState
        icon={Inbox}
        title="No issues yet"
        description="Issues created in this team will appear here. Issue tracking arrives in the next milestone."
      />
    </div>
  )
}
