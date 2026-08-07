/** Role of a user within a team (mirrors backend `TeamRole` enum). */
export type TeamRole = 'admin' | 'member' | 'guest'

/** Shape of the backend `GET /teams` list item (TeamResponse + OrmBaseModel). */
export interface Team {
  id: string
  name: string
  /** Short uppercase key used as the URL segment and issue-identifier prefix (e.g. `ENG`). */
  key: string
  /** Per-team monotonic counter used to mint issue identifiers (`<key>-<seq>`). */
  issue_sequence: number
  /**
   * The requesting user's role in this team. Present on list items so the SPA
   * can gate role-based UI (writes for guests, admin-only actions for members)
   * without a second request (VAL-CROSS-025).
   */
  my_role: TeamRole
  created_at: string
  updated_at: string
  deleted_at: string | null
}

/** Shape of a paginated `Page<TeamResponse>` from fastapi_pagination. */
export interface TeamsResponse {
  items: Team[]
  total: number
  page: number
  size: number
  pages: number
}

/** Role rank for capability comparisons (higher = more privileged). */
const ROLE_RANK: Record<TeamRole, number> = { guest: 0, member: 1, admin: 2 }

/** True when `role` meets or exceeds `required` (e.g. can a guest write? member?). */
export function hasRole(role: TeamRole | undefined, required: TeamRole): boolean {
  if (!role) return false
  return ROLE_RANK[role] >= ROLE_RANK[required]
}
