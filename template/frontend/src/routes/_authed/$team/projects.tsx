import { createFileRoute } from '@tanstack/react-router'
import { Folder } from 'lucide-react'
import { EmptyState } from '@/components/EmptyState'

/**
 * Projects view (M2). Empty state for M0.
 */
export const Route = createFileRoute('/_authed/$team/projects')({
  component: ProjectsView,
})

function ProjectsView() {
  return (
    <div className="p-6">
      <h1 className="mb-4 text-lg font-semibold text-foreground">Projects</h1>
      <EmptyState
        icon={Folder}
        title="No projects yet"
        description="Group related issues into projects. Project tracking arrives in a later milestone."
      />
    </div>
  )
}
