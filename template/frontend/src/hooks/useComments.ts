import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
} from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'
import { isAuthenticated } from '@/lib/auth'
import { toastApiError } from '@/lib/error-handler'
import type {
  Comment,
  CommentsResponse,
  CreateCommentInput,
  UpdateCommentInput,
  DeleteCommentInput,
} from '@/types/comment'

/** Prefix marking an optimistically-inserted comment (before the POST settles). */
export const OPTIMISTIC_COMMENT_PREFIX = 'optimistic-'

/** Polling interval (ms) — keeps the thread fresh without websockets. */
const COMMENTS_REFETCH_INTERVAL = 8000

/** Page size for the comment thread (fastapi_pagination caps `size` at 100). */
const COMMENTS_PAGE_SIZE = 50

/**
 * Fetch the comment thread for an issue (`GET /comments?issue_id=<id>`).
 *
 * The backend defaults to newest-first (``order_by=-created_at``) so the most
 * recent comment renders at the top (VAL-COMMENTS-003). Polls on a short
 * interval so a comment added/edited/removed elsewhere reconciles without a
 * manual refresh (VAL-COMMENTS-001, VAL-PERF-004).
 */
export function useComments(issueId: string | undefined, teamId: string | undefined) {
  return useQuery<CommentsResponse, Error>({
    queryKey: queryKeys.comments.forIssue(issueId!),
    queryFn: () => {
      const sp = new URLSearchParams()
      sp.set('issue_id', issueId!)
      sp.set('size', String(COMMENTS_PAGE_SIZE))
      return api.get<CommentsResponse>(`${API.COMMENTS.LIST}?${sp.toString()}`)
    },
    enabled: !!issueId && !!teamId && isAuthenticated(),
    refetchInterval: COMMENTS_REFETCH_INTERVAL,
    refetchOnWindowFocus: true,
  })
}

type CommentsContext = {
  issueId: string
  previous: CommentsResponse | undefined
}

/**
 * Prepend an optimistic comment to the thread (newest-first).
 *
 * Used by {@link useCreateComment} so a newly-added comment appears at the top
 * before the POST settles (VAL-COMMENTS-001). The optimistic entry is later
 * reconciled to the server-generated id/timestamp by the settle invalidation.
 */
function prependOptimistic(
  old: CommentsResponse | undefined,
  optimistic: Comment,
): CommentsResponse {
  const items = old?.items ?? []
  return {
    items: [optimistic, ...items],
    total: (old?.total ?? 0) + 1,
    page: old?.page ?? 1,
    size: old?.size ?? COMMENTS_PAGE_SIZE,
    pages: old?.pages ?? 1,
  }
}

/**
 * Add a comment. Optimistically inserts the new comment at the top of the
 * thread (newest-first) so it appears instantly; rolls back on error and
 * invalidates on settle to reconcile the server-generated id/timestamp
 * (VAL-COMMENTS-001).
 *
 * The composer must block empty/whitespace bodies before calling this
 * (VAL-COMMENTS-002); the backend also rejects them with 422 (defense-in-depth).
 */
export function useCreateComment() {
  const qc = useQueryClient()

  return useMutation<Comment, Error, CreateCommentInput, CommentsContext>({
    mutationFn: (input) =>
      api.post<Comment>(API.COMMENTS.CREATE, {
        issue_id: input.issue_id,
        body: input.body,
      }),
    onMutate: async (input) => {
      const key = queryKeys.comments.forIssue(input.issue_id)
      await qc.cancelQueries({ queryKey: key })
      const previous = qc.getQueryData<CommentsResponse>(key)

      const now = new Date().toISOString()
      const optimistic: Comment = {
        id: `${OPTIMISTIC_COMMENT_PREFIX}${crypto.randomUUID()}`,
        issue_id: input.issue_id,
        author_id: input.author.id,
        body: input.body,
        author: input.author,
        created_at: now,
        updated_at: now,
      }
      qc.setQueryData<CommentsResponse>(key, prependOptimistic(previous, optimistic))

      return { issueId: input.issue_id, previous }
    },
    onError: (error, _input, context) => {
      if (context) {
        qc.setQueryData(
          queryKeys.comments.forIssue(context.issueId),
          context.previous,
        )
      }
      toastApiError(error, 'Failed to add comment')
    },
    onSettled: (_data, _error, input) => {
      void qc.invalidateQueries({
        queryKey: queryKeys.comments.forIssue(input.issue_id),
      })
    },
  })
}

type UpdateContext = {
  id: string
  issueId: string | undefined
  previous: CommentsResponse | undefined
}

/**
 * Edit a comment's body **in place** — optimistic patch of the matching comment
 * (no duplicate added, no reload). Rolls back on error and invalidates on settle
 * so the edited timestamp reconciles (VAL-COMMENTS-005).
 */
export function useUpdateComment() {
  const qc = useQueryClient()

  return useMutation<Comment, Error, UpdateCommentInput, UpdateContext>({
    mutationFn: (input) =>
      api.patch<Comment>(API.COMMENTS.DETAIL(input.id), { body: input.body }),
    onMutate: async (input) => {
      const issueId = findIssueIdForComment(qc, input.id)
      if (issueId) {
        const key = queryKeys.comments.forIssue(issueId)
        await qc.cancelQueries({ queryKey: key })
        const previous = qc.getQueryData<CommentsResponse>(key)
        qc.setQueryData<CommentsResponse>(key, patchCommentBody(previous, input.id, input.body))
        return { id: input.id, issueId, previous }
      }
      return { id: input.id, issueId: undefined, previous: undefined }
    },
    onError: (_error, _input, context) => {
      if (context?.issueId) {
        qc.setQueryData(
          queryKeys.comments.forIssue(context.issueId),
          context.previous,
        )
      }
      toastApiError(_error, 'Failed to edit comment')
    },
    onSettled: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.comments.all })
    },
  })
}

type DeleteContext = {
  id: string
  issueId: string | undefined
  previous: CommentsResponse | undefined
}

/**
 * Delete a comment. Optimistically removes it from the thread; rolls back on
 * error and invalidates on settle (VAL-COMMENTS-006).
 */
export function useDeleteComment() {
  const qc = useQueryClient()

  return useMutation<void, Error, DeleteCommentInput, DeleteContext>({
    mutationFn: (input) => api.delete<void>(API.COMMENTS.DETAIL(input.id)),
    onMutate: async (input) => {
      const issueId = findIssueIdForComment(qc, input.id)
      if (issueId) {
        const key = queryKeys.comments.forIssue(issueId)
        await qc.cancelQueries({ queryKey: key })
        const previous = qc.getQueryData<CommentsResponse>(key)
        qc.setQueryData<CommentsResponse>(key, removeComment(previous, input.id))
        return { id: input.id, issueId, previous }
      }
      return { id: input.id, issueId: undefined, previous: undefined }
    },
    onError: (_error, _input, context) => {
      if (context?.issueId) {
        qc.setQueryData(
          queryKeys.comments.forIssue(context.issueId),
          context.previous,
        )
      }
      toastApiError(_error, 'Failed to delete comment')
    },
    onSettled: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.comments.all })
    },
  })
}

// ---------------------------------------------------------------------------
// Cache helpers
// ---------------------------------------------------------------------------

/**
 * Locate the issue id whose comment cache contains ``commentId``. Needed by
 * update/delete to find the right thread cache (the mutation only knows the
 * comment id, not the issue).
 */
function findIssueIdForComment(qc: QueryClient, commentId: string): string | undefined {
  const caches = qc.getQueriesData<CommentsResponse>({ queryKey: queryKeys.comments.all })
  for (const [key, data] of caches) {
    if (data?.items.some((c) => c.id === commentId)) {
      // key shape: ['comments', 'issue', issueId]
      const issueId = key[2]
      return typeof issueId === 'string' ? issueId : undefined
    }
  }
  return undefined
}

/** Patch a comment's body in place across the thread cache. */
function patchCommentBody(
  old: CommentsResponse | undefined,
  id: string,
  body: string,
): CommentsResponse | undefined {
  if (!old) return old
  return {
    ...old,
    items: old.items.map((c) => (c.id === id ? { ...c, body } : c)),
  }
}

/** Remove a comment from the thread cache and decrement the total. */
function removeComment(
  old: CommentsResponse | undefined,
  id: string,
): CommentsResponse | undefined {
  if (!old) return old
  const items = old.items.filter((c) => c.id !== id)
  return { ...old, items, total: Math.max(0, old.total - 1) }
}
