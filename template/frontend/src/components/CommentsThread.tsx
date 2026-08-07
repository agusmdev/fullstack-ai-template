import { useState } from 'react'
import { MessageSquare, Loader2, Pencil, Trash2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import {
  useComments,
  useCreateComment,
  useUpdateComment,
  useDeleteComment,
} from '@/hooks/useComments'
import { useUser } from '@/hooks/useUser'
import { useTeams } from '@/hooks/useTeams'
import { hasRole } from '@/types/team'
import { cn } from '@/lib/utils'
import type { Comment } from '@/types/comment'

interface CommentsThreadProps {
  /** The issue whose comment thread to display. */
  issueId: string
  /** The issue's team id (used to resolve the current user's role). */
  teamId: string
}

/**
 * Format an ISO timestamp into a compact, human-readable relative time. Never
 * returns `Invalid Date` — falls back to an absolute date on parse failure
 * (VAL-COMMENTS-004).
 */
export function formatCommentTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  const diffSec = Math.round((Date.now() - d.getTime()) / 1000)
  if (diffSec < 60) return 'just now'
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`
  if (diffSec < 604800) return `${Math.floor(diffSec / 86400)}d ago`
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

/**
 * Comments thread — shown in the issue detail drawer.
 *
 * - Lists comments newest-first with the author (name/initials) and a
 *   human-readable timestamp (VAL-COMMENTS-003, VAL-COMMENTS-004).
 * - Explicit empty state when the issue has no comments (VAL-COMMENTS-007).
 * - Composer blocks empty/whitespace-only bodies (VAL-COMMENTS-002); new
 *   comments appear at the top via an optimistic insert (VAL-COMMENTS-001).
 * - Edit-in-place updates the body without duplicating or reloading
 *   (VAL-COMMENTS-005); delete removes the comment (VAL-COMMENTS-006).
 * - Edit/delete are scoped to the author or a team admin; others see no
 *   controls (VAL-COMMENTS-008).
 */
export function CommentsThread({ issueId, teamId }: CommentsThreadProps) {
  const commentsQuery = useComments(issueId, teamId)
  const createComment = useCreateComment()
  const { data: user } = useUser()
  const { data: teamsData } = useTeams()

  const team = (teamsData?.items ?? []).find((t) => t.id === teamId)
  const role = team?.my_role
  const canWrite = hasRole(role, 'member')

  const comments = commentsQuery.data?.items ?? []
  const [draft, setDraft] = useState('')
  const trimmed = draft.trim()

  const handleAdd = async () => {
    if (!trimmed || !user) return
    const body = draft
    setDraft('')
    try {
      await createComment.mutateAsync({
        issue_id: issueId,
        body,
        author: {
          id: user.id,
          display_name: user.display_name,
          email: user.email,
        },
      })
    } catch {
      // Error toast handled by the hook.
    }
  }

  return (
    <div className="mt-6 border-t border-border pt-4">
      <div className="mb-2 flex items-center gap-1.5">
        <MessageSquare className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="text-xs font-medium text-muted-foreground">Comments</span>
        {comments.length > 0 && (
          <span className="text-xs text-muted-foreground/70">{comments.length}</span>
        )}
      </div>

      {/* Thread */}
      {commentsQuery.isLoading ? (
        <div className="flex items-center gap-1.5 px-1 py-1 text-xs text-muted-foreground">
          <Loader2 className="h-3 w-3 animate-spin" />
          Loading…
        </div>
      ) : comments.length === 0 ? (
        <p className="px-1 py-1 text-xs text-muted-foreground/60">
          No comments yet — start the discussion.
        </p>
      ) : (
        <div className="flex flex-col gap-3" data-testid="comments-list">
          {comments.map((comment) => (
            <CommentItem
              key={comment.id}
              comment={comment}
              currentUserId={user?.id}
              canModerate={hasRole(role, 'admin')}
            />
          ))}
        </div>
      )}

      {/* Composer (members/admins only — guests are read-only) */}
      {canWrite && (
        <div className="mt-3 flex flex-col gap-2" data-testid="comment-composer">
          <Textarea
            value={draft}
            rows={2}
            placeholder="Write a comment…"
            aria-label="Comment"
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                e.preventDefault()
                void handleAdd()
              }
            }}
          />
          <div className="flex justify-end gap-2">
            <Button
              size="sm"
              onClick={handleAdd}
              disabled={!trimmed || createComment.isPending}
              data-testid="comment-submit"
            >
              {createComment.isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : null}
              Comment
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

interface CommentItemProps {
  comment: Comment
  currentUserId: string | undefined
  /** True if the current user is a team admin (can edit/delete any comment). */
  canModerate: boolean
}

/**
 * A single comment row with edit-in-place and delete (author/admin only).
 */
function CommentItem({ comment, currentUserId, canModerate }: CommentItemProps) {
  const updateComment = useUpdateComment()
  const deleteComment = useDeleteComment()
  const [editing, setEditing] = useState(false)
  const [editDraft, setEditDraft] = useState(comment.body)
  const [confirmingDelete, setConfirmingDelete] = useState(false)

  const isAuthor = !!currentUserId && comment.author_id === currentUserId
  const canModify = isAuthor || canModerate
  const busy = updateComment.isPending || deleteComment.isPending

  const authorName = comment.author.display_name?.trim() || comment.author.email || 'Unknown'

  const startEdit = () => {
    setEditDraft(comment.body)
    setEditing(true)
  }
  const cancelEdit = () => {
    setEditDraft(comment.body)
    setEditing(false)
  }
  const commitEdit = async () => {
    const next = editDraft.trim()
    if (!next || next === comment.body) {
      cancelEdit()
      return
    }
    setEditing(false)
    try {
      await updateComment.mutateAsync({ id: comment.id, body: next })
    } catch {
      // Error toast handled by the hook; restore the draft.
      setEditDraft(comment.body)
    }
  }
  const handleDelete = async () => {
    setConfirmingDelete(false)
    try {
      await deleteComment.mutateAsync({ id: comment.id })
    } catch {
      // Error toast handled by the hook.
    }
  }

  return (
    <div className="group flex gap-2.5" data-testid="comment-item">
      <Avatar name={authorName} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-xs font-medium text-foreground" data-testid="comment-author">
            {authorName}
          </span>
          <span className="shrink-0 text-[11px] text-muted-foreground" data-testid="comment-time">
            {formatCommentTime(comment.created_at)}
          </span>
        </div>

        {editing ? (
          <div className="mt-1 flex flex-col gap-1.5">
            <Textarea
              value={editDraft}
              rows={3}
              autoFocus
              aria-label="Edit comment"
              onChange={(e) => setEditDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                  e.preventDefault()
                  void commitEdit()
                } else if (e.key === 'Escape') {
                  cancelEdit()
                }
              }}
            />
            <div className="flex gap-2">
              <Button size="sm" onClick={commitEdit} disabled={!editDraft.trim() || busy}>
                Save
              </Button>
              <Button size="sm" variant="outline" onClick={cancelEdit} disabled={busy}>
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <p className="mt-0.5 whitespace-pre-wrap break-words text-xs text-foreground" data-testid="comment-body">
            {comment.body}
          </p>
        )}

        {/* Edit / delete controls — author or admin only (VAL-COMMENTS-008) */}
        {canModify && !editing && (
          <div className="mt-1 flex items-center gap-2">
            {!confirmingDelete ? (
              <>
                <button
                  type="button"
                  className="flex items-center gap-1 text-[11px] text-muted-foreground opacity-0 transition-opacity hover:text-foreground group-hover:opacity-100"
                  onClick={startEdit}
                  disabled={busy}
                  data-testid="comment-edit"
                >
                  <Pencil className="h-3 w-3" />
                  Edit
                </button>
                <button
                  type="button"
                  className="flex items-center gap-1 text-[11px] text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100"
                  onClick={() => setConfirmingDelete(true)}
                  disabled={busy}
                  data-testid="comment-delete"
                >
                  <Trash2 className="h-3 w-3" />
                  Delete
                </button>
              </>
            ) : (
              <div className="flex items-center gap-2" data-testid="comment-delete-confirm">
                <span className="text-[11px] text-muted-foreground">Delete this comment?</span>
                <Button size="sm" variant="destructive" onClick={handleDelete} disabled={busy} data-testid="comment-delete-confirm-action">
                  Delete
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setConfirmingDelete(false)} disabled={busy}>
                  <X className="h-3 w-3" />
                  Cancel
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

/** A small initials avatar (no external dependency). */
function Avatar({ name }: { name: string }) {
  const initials = name
    .split(/\s+/)
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()
  return (
    <div
      className={cn(
        'flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-muted text-[10px] font-medium text-muted-foreground',
      )}
      aria-hidden="true"
    >
      {initials || '?'}
    </div>
  )
}
