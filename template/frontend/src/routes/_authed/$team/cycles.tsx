import { createFileRoute } from '@tanstack/react-router'
import { Repeat2 } from 'lucide-react'
import { EmptyState } from '@/components/EmptyState'

/**
 * Cycles view (M2). Empty state for M0.
 */
export const Route = createFileRoute('/_authed/$team/cycles')({
  component: CyclesView,
})

function CyclesView() {
  return (
    <div className="p-6">
      <h1 className="mb-4 text-lg font-semibold text-foreground">Cycles</h1>
      <EmptyState
        icon={Repeat2}
        title="No cycles yet"
        description="Cycles are time-boxed sprints for your team. Cycle tracking arrives in a later milestone."
      />
    </div>
  )
}
