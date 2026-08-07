import { useState } from 'react'
import { createFileRoute, useParams, Link } from '@tanstack/react-router'
import { ArrowLeft, Folder, Inbox, Loader2, Pencil } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { IssueList } from '@/components/IssueList'
import { IssueListSkeleton } from '@/components/IssueListSkeleton'
import { IssueDetailDrawer } from '@/components/IssueDetailDrawer'
import { ProjectFormDialog } from '@/components/ProjectFormDialog'
import { useTeams } from '@/hooks/useTeams'
import { useUser } from '@/hooks/useUser'
import { useTeamRole } from '@/hooks/useTeamRole'
import { useProject, useProjects } from '@/hooks/useProjects'
import { useCycles } from '@/hooks/useCycles'
import { useIssues, flattenIssues, issuesTotal } from '@/hooks/useIssues'
import { useWorkflowStates } from '@/hooks/useWorkflowStates'
import { useLabels } from '@/hooks/useLabels'
import { projectStatusOption } from '@/types/project'
import { DEFAULT_SORT_KEY, type Issue } from '@/types/issue'

export const Route = createFileRoute('/_authed/$team/project/$id')({
  component: ProjectDetailView,
})

/** Format an ISO date string into a short date (never Invalid Date). */
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

/**
 * Project detail view — shows the project header and lists **only** that
 * project's issues (filtered server-side by ``project_id``) (VAL-PROJECTS-006).
 *
 * Issues assigned from the drawer appear here within invalidation/polling and
 * persist on reload. The project picker in the drawer is the assign/remove
 * surface (VAL-PROJECTS-007, VAL-PROJECTS-008).
 */
function ProjectDetailView() {
  const { team: teamKey, id: projectId } = useParams({ strict: false })
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null)
  const [editOpen, setEditOpen] = useState(false)

  const { data: teamsData, isLoading: teamsLoading } = useTeams()
  const { data: user } = useUser()
  const { canWrite } = useTeamRole(teamKey)
  const teamObj = (teamsData?.items ?? []).find((t) => t.key === teamKey)
  const teamId = teamObj?.id

  const projectQuery = useProject(projectId)
  const statesQuery = useWorkflowStates(teamId)
  const labelsQuery = useLabels(teamId)
  const projectsQuery = useProjects(teamId)
  const cyclesQuery = useCycles(teamId)
  // Fetch only this project's issues (server-side project_id filter).
  const issuesQuery = useIssues(teamId, {
    project_id: projectId,
    sort: DEFAULT_SORT_KEY,
  })

  const project = projectQuery.data
  const workflowStates = statesQuery.data?.items ?? []
  const labels = labelsQuery.data?.items ?? []
  const projects = projectsQuery.data?.items ?? []
  const cycles = cyclesQuery.data?.items ?? []
  const issues = flattenIssues(issuesQuery.data)
  const total = issuesTotal(issuesQuery.data)

  const members = user
    ? [{ id: user.id, name: user.display_name || user.email }]
    : []
  const assigneeNames: Record<string, string> = Object.fromEntries(
    members.map((m) => [m.id, m.name]),
  )
  const projectNames: Record<string, string> = Object.fromEntries(
    projects.map((p) => [p.id, p.name]),
  )

  const initialLoading =
    teamsLoading || (teamId ? projectQuery.isLoading : true)

  if (initialLoading) {
    return (
      <div className="flex items-center gap-2 p-6 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading project…
      </div>
    )
  }

  if (projectQuery.isError || !project) {
    return (
      <div className="p-6">
        <ErrorState
          error={projectQuery.error ?? new Error('Project not found')}
          title="Project not found"
        />
        <div className="mt-3 flex justify-center">
          <Button asChild variant="outline" size="sm">
            <Link to="/$team/projects" params={{ team: teamKey ?? '' }}>
              <ArrowLeft className="h-4 w-4" />
              Back to projects
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  const status = projectStatusOption(project.status)
  const lead = members.find((m) => m.id === project.lead_id)

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-border px-6 py-3">
        <div className="mb-2 flex items-center gap-2">
          <Button asChild variant="ghost" size="sm" className="h-7 gap-1 px-2 text-muted-foreground">
            <Link to="/$team/projects" params={{ team: teamKey ?? '' }}>
              <ArrowLeft className="h-3.5 w-3.5" />
              Projects
            </Link>
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Folder className="h-4 w-4 text-muted-foreground" />
          <h1 className="text-lg font-semibold text-foreground">{project.name}</h1>
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] ${
              status.terminal
                ? 'bg-muted text-muted-foreground'
                : 'bg-primary/10 text-primary'
            }`}
          >
            {status.label}
          </span>
          <Button
            variant="outline"
            size="sm"
            className="ml-auto h-7 gap-1 px-2"
            onClick={() => setEditOpen(true)}
            disabled={!canWrite}
          >
            <Pencil className="h-3.5 w-3.5" />
            Edit
          </Button>
        </div>
        <div className="mt-1 flex items-center gap-4 text-xs text-muted-foreground">
          <span>Lead: {lead?.name ?? 'Unassigned'}</span>
          <span>Target: {formatDate(project.target_date)}</span>
          <span>{total} issue{total === 1 ? '' : 's'}</span>
        </div>
      </div>

      {/* Body — only this project's issues (VAL-PROJECTS-006) */}
      <div className="flex-1 overflow-auto p-6">
        {statesQuery.isLoading ? (
          <IssueListSkeleton groups={Math.min(workflowStates.length || 3, 5)} />
        ) : issuesQuery.isError ? (
          <ErrorState
            error={issuesQuery.error}
            onRetry={() => issuesQuery.refetch()}
            title="Couldn't load issues"
          />
        ) : total === 0 ? (
          <EmptyState
            icon={Inbox}
            title="No issues in this project"
            description="Assign issues to this project from the issue drawer to see them here."
          />
        ) : (
          <IssueList
            issues={issues}
            workflowStates={workflowStates}
            assigneeNames={assigneeNames}
            projectNames={projectNames}
            onSelectIssue={setSelectedIssue}
          />
        )}
      </div>

      <IssueDetailDrawer
        open={!!selectedIssue}
        onOpenChange={(o) => !o && setSelectedIssue(null)}
        issueId={selectedIssue?.id ?? null}
        initialIssue={selectedIssue ?? undefined}
        teamId={teamId ?? ''}
        workflowStates={workflowStates}
        labels={labels}
        projects={projects}
        cycles={cycles}
        members={members}
      />

      <ProjectFormDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        teamId={teamId ?? ''}
        members={members}
        project={project}
      />
    </div>
  )
}
