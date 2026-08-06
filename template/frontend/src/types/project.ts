/** Lifecycle status of a project (mirrors backend `ProjectStatus`). */

/** Canonical project status set, ordered by lifecycle. */
export interface ProjectStatusOption {
  value: string
  label: string
  terminal: boolean
}

/**
 * Canonical project statuses.
 *
 * ``planned`` and ``started`` are non-terminal (active);
 * ``completed`` and ``canceled`` are terminal.
 */
export const PROJECT_STATUSES: readonly ProjectStatusOption[] = [
  { value: 'planned', label: 'Planned', terminal: false },
  { value: 'started', label: 'In Progress', terminal: false },
  { value: 'completed', label: 'Completed', terminal: true },
  { value: 'canceled', label: 'Canceled', terminal: true },
] as const

/** Default project status (non-terminal). */
export const DEFAULT_PROJECT_STATUS = 'planned' as const

/** Resolve a status value to its option (falls back to Planned). */
export function projectStatusOption(value: string | undefined): ProjectStatusOption {
  return (
    PROJECT_STATUSES.find((s) => s.value === value) ?? PROJECT_STATUSES[0]
  )
}

/** True when the status is a terminal (completed/canceled). */
export function isTerminalProjectStatus(value: string | undefined): boolean {
  return projectStatusOption(value).terminal
}

/** Shape of the backend `ProjectResponse`. */
export interface Project {
  id: string
  team_id: string
  name: string
  status: string
  lead_id: string | null
  target_date: string | null
  description: string | null
  created_at: string
  updated_at: string
}

/** Shape of a paginated `Page<ProjectResponse>` from fastapi_pagination. */
export interface ProjectsResponse {
  items: Project[]
  total: number
  page: number
  size: number
  pages: number
}
