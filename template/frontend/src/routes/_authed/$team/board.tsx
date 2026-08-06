import { createFileRoute } from '@tanstack/react-router'
import { LayoutGrid } from 'lucide-react'
import { EmptyState } from '@/components/EmptyState'

/**
 * Board view — kanban by workflow status (M3). Empty state for M0.
 */
export const Route = createFileRoute('/_authed/$team/board')({
  component: BoardView,
})

function BoardView() {
  return (
    <div className="p-6">
      <h1 className="mb-4 text-lg font-semibold text-foreground">Board</h1>
      <EmptyState
        icon={LayoutGrid}
        title="No issues to display"
        description="The kanban board groups issues by status. It fills in once issues exist."
      />
    </div>
  )
}
