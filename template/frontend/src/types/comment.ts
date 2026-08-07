/** Lightweight author info embedded in a comment response (AuthorBrief). */
export interface AuthorBrief {
  id: string
  display_name: string
  email: string
}

/**
 * A discussion comment on an issue.
 *
 * The author is set server-side from the authenticated user; edit/delete are
 * restricted to the author or a team admin (VAL-COMMENTS-005/006/008).
 */
export interface Comment {
  id: string
  issue_id: string
  author_id: string
  body: string
  author: AuthorBrief
  created_at: string
  updated_at: string
}

/** Shape of a paginated `Page<CommentResponse>` from fastapi_pagination. */
export interface CommentsResponse {
  items: Comment[]
  total: number
  page: number
  size: number
  pages: number
}

/**
 * Payload for `POST /comments`. ``author`` is never sent to the API — it carries
 * the resolved current-user brief so the optimistically-inserted comment can
 * render the author instantly before the POST settles (the real comment
 * refetch reconciles the server-generated id/timestamp afterwards).
 */
export interface CreateCommentInput {
  issue_id: string
  body: string
  /** Optimistic-only: resolved author for instant display. Not serialized. */
  author: AuthorBrief
}

/** Payload for `PATCH /comments/:id` (edit body in place — VAL-COMMENTS-005). */
export interface UpdateCommentInput {
  id: string
  body: string
}

/** Payload for `DELETE /comments/:id` (VAL-COMMENTS-006). */
export interface DeleteCommentInput {
  id: string
}
