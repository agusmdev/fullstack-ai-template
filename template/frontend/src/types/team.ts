/** Shape of the backend `GET /teams` list item (TeamResponse + OrmBaseModel). */
export interface Team {
  id: string
  name: string
  /** Short uppercase key used as the URL segment and issue-identifier prefix (e.g. `ENG`). */
  key: string
  /** Per-team monotonic counter used to mint issue identifiers (`<key>-<seq>`). */
  issue_sequence: number
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
