/** Lightweight issue info embedded in a dependency response (DependencyIssueBrief). */
export interface DependencyIssueBrief {
  id: string
  identifier: string
  title: string
  priority: number
  status_id: string
}

/**
 * A 'blocks' dependency between two issues.
 *
 * "A blocks B" → ``blocker`` is A (the issue that blocks), ``blocked`` is B
 * (the issue that is blocked). The relationship is a single record, so deleting
 * it detaches both sides (VAL-DEPS-002/004).
 */
export interface IssueDependency {
  id: string
  blocker_id: string
  blocked_id: string
  relation: string
  blocker: DependencyIssueBrief
  blocked: DependencyIssueBrief
  created_at: string
  updated_at: string
}

/** Shape of a paginated `Page<IssueDependencyResponse>` from fastapi_pagination. */
export interface IssueDependenciesResponse {
  items: IssueDependency[]
  total: number
  page: number
  size: number
  pages: number
}

/** Payload for `POST /issue-dependencies` ("A blocks B"). */
export interface CreateIssueDependencyInput {
  /** The issue that blocks (A in 'A blocks B'). */
  blocker_id: string
  /** The issue that is blocked (B in 'A blocks B'). */
  blocked_id: string
  /** The current issue's team (scopes optimistic cache invalidation). */
  team_id: string
}

/** Payload for `DELETE /issue-dependencies/:id`. */
export interface DeleteIssueDependencyInput {
  id: string
  team_id: string
}
