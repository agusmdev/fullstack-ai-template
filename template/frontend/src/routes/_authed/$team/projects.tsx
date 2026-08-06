import { useState } from 'react'
import { createFileRoute, useParams, Link } from '@tanstack/react-router'
import { Plus, Folder, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { ProjectFormDialog } from '@/components/ProjectFormDialog'
import { useTeams } from '@/hooks/useTeams'
import { useUser } from '@/hooks/useUser'
import { useTeamRole } from '@/hooks/useTeamRole'
import { useProjects } from '@/hooks/useProjects'
import {
  projectStatusOption,
  type Project,
} from '@/types/project'

export const Route = createFileRoute('/_authed/$team/projects')({
  component: ProjectsView,
})

/** Format an ISO date string into a short, human-readable date (never Invalid Date). */
function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

/** Resolve a member's display name from the known members. */
function memberName(
  members: { id: string; name: string }[],
  id: string | null | undefined,
): string | null {
  if (!id) return null
  return members.find((m) => m.id === id)?.name ?? null
}

/**
 * Projects view — the team-scoped projects list.
 *
 * - Shows every project in the team with its status, lead, and target date.
 * - Empty state with a "New Project" CTA when there are no projects
 *   (VAL-PROJECTS-005).
 * - Create-project dialog (name required, status, lead picker, target date)
 *   (VAL-PROJECTS-001–004).
 * - Each project links to its detail view.
 */
function ProjectsView() {
  const { team: teamKey } = useParams({ strict: false })
  const [createOpen, setCreateOpen] = useState(false)

  const { data: teamsData, isLoading: teamsLoading } = useTeams()
  const { data: user } = useUser()
  const { canWrite } = useTeamRole(teamKey)

  const teamObj = (teamsData?.items ?? []).find((t) => t.key === teamKey)
  const teamId = teamObj?.id

  const projectsQuery = useProjects(teamId)
  const projects = projectsQuery.data?.items ?? []
  const total = projectsQuery.data?.total ?? 0

  const members = user
    ? [{ id: user.id, name: user.display_name || user.email }]
    : []

  const initialLoading = teamsLoading || (teamId ? projectsQuery.isLoading : true)

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-6 py-3">
        <h1 className="text-base font-semibold text-foreground">Projects</h1>
        <Button size="sm" onClick={() => setCreateOpen(true)} disabled={!canWrite}>
          <Plus className="h-4 w-4" />
          New project
        </Button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-auto p-6">
        {initialLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading projects…
          </div>
        ) : projectsQuery.isError ? (
          <ErrorState
            error={projectsQuery.error}
            onRetry={() => projectsQuery.refetch()}
            title="Couldn't load projects"
          />
        ) : total === 0 ? (
          <EmptyState
            icon={Folder}
            title="No projects yet"
            description="Group related issues into a project to track progress toward a shared goal."
            action={
              canWrite ? (
                <Button size="sm" onClick={() => setCreateOpen(true)}>
                  <Plus className="h-4 w-4" />
                  New project
                </Button>
              ) : (
                <p className="text-xs text-muted-foreground">
                  Guests have read-only access to this team.
                </p>
              )
            }
          />
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((project: Project) => {
              const status = projectStatusOption(project.status)
              const lead = memberName(members, project.lead_id)
              return (
                <Link
                  key={project.id}
                  to="/$team/project/$id"
                  params={{ team: teamKey ?? '', id: project.id }}
                  className="flex flex-col gap-2 rounded-lg border border-border bg-card p-4 no-underline transition-colors hover:bg-accent/50"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="text-sm font-semibold text-foreground">
                      {project.name}
                    </h3>
                    <span
                      className={`inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[11px] ${
                        status.terminal
                          ? 'bg-muted text-muted-foreground'
                          : 'bg-primary/10 text-primary'
                      }`}
                    >
                      {status.label}
                    </span>
                  </div>
                  {project.description && (
                    <p className="line-clamp-2 text-xs text-muted-foreground">
                      {project.description}
                    </p>
                  )}
                  <div className="mt-auto flex items-center justify-between pt-2 text-xs text-muted-foreground">
                    <span>{lead ?? 'No lead'}</span>
                    <span>{formatDate(project.target_date)}</span>
                  </div>
                </Link>
              )
            })}
          </div>
        )}
      </div>

      <ProjectFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        teamId={teamId ?? ''}
        members={members}
      />
    </div>
  )
}
