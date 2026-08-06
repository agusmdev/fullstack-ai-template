import {
  useMutation,
  useQuery,
  useQueryClient,
  keepPreviousData,
} from '@tanstack/react-query'
import { toast } from 'sonner'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'
import { isAuthenticated } from '@/lib/auth'
import { toastApiError } from '@/lib/error-handler'
import type {
  Project,
  ProjectsResponse,
} from '@/types/project'

/**
 * Polling interval (ms) — keeps the active project list fresh.
 */
const PROJECTS_REFETCH_INTERVAL = 10000

/** Payload sent to `POST /projects`. */
export interface CreateProjectInput {
  team_id: string
  name: string
  status?: string
  lead_id?: string | null
  target_date?: string | null
  description?: string | null
}

/** Partial patch for `PATCH /projects/:id`. */
export interface UpdateProjectInput {
  id: string
  team_id: string
  name?: string
  status?: string
  lead_id?: string | null
  target_date?: string | null
  description?: string | null
}

/**
 * Fetch a team's projects (`GET /projects?team_id=`).
 *
 * Only enabled when a teamId and auth token are present. Polls on a short
 * interval so project lists stay fresh after an issue is assigned/unassigned.
 */
export function useProjects(teamId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.projects.list(teamId),
    queryFn: () =>
      api.get<ProjectsResponse>(
        `${API.PROJECTS.LIST}?team_id=${teamId}&size=100&order_by=-created_at`,
      ),
    enabled: !!teamId && isAuthenticated(),
    placeholderData: keepPreviousData,
    staleTime: 30 * 1000,
    refetchInterval: PROJECTS_REFETCH_INTERVAL,
    refetchOnWindowFocus: true,
  })
}

/**
 * Fetch a single project by ID (`GET /projects/:id`).
 */
export function useProject(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.projects.detail(projectId!),
    queryFn: () => api.get<Project>(API.PROJECTS.DETAIL(projectId!)),
    enabled: !!projectId && isAuthenticated(),
  })
}

/**
 * Resolve project IDs to names for badge display. Returns a function
 * ``projectId → Project | undefined`` from the cached list.
 */
export function useProjectLookup(teamId: string | undefined) {
  const { data } = useProjects(teamId)
  const map = new Map((data?.items ?? []).map((p) => [p.id, p]))
  return (projectId: string | null | undefined): Project | undefined =>
    projectId ? map.get(projectId) : undefined
}

/**
 * Create a project. Invalidates the team's project list so the new project
 * appears (VAL-PROJECTS-001).
 */
export function useCreateProject() {
  const qc = useQueryClient()

  return useMutation<Project, Error, CreateProjectInput>({
    mutationFn: (input) => api.post<Project>(API.PROJECTS.CREATE, input),
    onSuccess: () => {
      toast.success('Project created')
    },
    onError: (error) => {
      toastApiError(error, 'Failed to create project')
    },
    onSettled: (_data, _error, input) => {
      void qc.invalidateQueries({
        queryKey: queryKeys.projects.list(input.team_id),
      })
    },
  })
}

/**
 * Update a project (optimistic). Applies the patch to the list + detail caches
 * instantly and rolls back on error.
 */
export function useUpdateProject() {
  const qc = useQueryClient()

  return useMutation<Project, Error, UpdateProjectInput>({
    mutationFn: (input) => {
      // Omit id + team_id (scoping/routing keys) from the PATCH body.
      const body: Record<string, unknown> = { ...input }
      delete body.id
      delete body.team_id
      return api.patch<Project>(API.PROJECTS.DETAIL(input.id), body)
    },
    onSuccess: () => {
      toast.success('Project updated')
    },
    onError: (error) => {
      toastApiError(error, 'Failed to update project')
    },
    onSettled: (_data, _error, input) => {
      void qc.invalidateQueries({
        queryKey: queryKeys.projects.detail(input.id),
      })
      void qc.invalidateQueries({
        queryKey: queryKeys.projects.list(input.team_id),
      })
    },
  })
}

/**
 * Delete a project (optimistic removal). Issues are detached server-side
 * (SET NULL); the issues list is invalidated to reflect the cleared badges.
 */
export function useDeleteProject() {
  const qc = useQueryClient()

  return useMutation<void, Error, { id: string; team_id: string }>({
    mutationFn: (input) => api.delete<void>(API.PROJECTS.DETAIL(input.id)),
    onSuccess: () => {
      toast.success('Project deleted')
    },
    onError: (error) => {
      toastApiError(error, 'Failed to delete project')
    },
    onSettled: (_data, _error, input) => {
      void qc.invalidateQueries({
        queryKey: queryKeys.projects.list(input.team_id),
      })
      void qc.removeQueries({
        queryKey: queryKeys.projects.detail(input.id),
      })
      // Issues may have had their project_id cleared (SET NULL on delete).
      void qc.invalidateQueries({ queryKey: queryKeys.issues.list(input.team_id) })
    },
  })
}
