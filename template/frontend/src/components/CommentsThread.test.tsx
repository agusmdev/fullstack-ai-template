import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { CommentsThread, formatCommentTime } from './CommentsThread'
import type { Comment } from '@/types/comment'

// Mock the hooks used by CommentsThread.
const hooks = vi.hoisted(() => ({
  useComments: vi.fn(),
  useCreateComment: vi.fn(),
  useUpdateComment: vi.fn(),
  useDeleteComment: vi.fn(),
  useUser: vi.fn(),
  useTeams: vi.fn(),
}))

vi.mock('@/hooks/useComments', () => ({
  useComments: hooks.useComments,
  useCreateComment: hooks.useCreateComment,
  useUpdateComment: hooks.useUpdateComment,
  useDeleteComment: hooks.useDeleteComment,
}))
vi.mock('@/hooks/useUser', () => ({ useUser: hooks.useUser }))
vi.mock('@/hooks/useTeams', () => ({ useTeams: hooks.useTeams }))

const noopMutation = {
  mutate: vi.fn(),
  mutateAsync: vi.fn(),
  isPending: false,
  isSuccess: false,
  isError: false,
}

function makeComment(
  id: string,
  body: string,
  authorId = 'me',
  authorName = 'Ada',
): Comment {
  return {
    id,
    issue_id: 'issue-1',
    author_id: authorId,
    body,
    author: { id: authorId, display_name: authorName, email: 'ada@x.com' },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  }
}

/** Default setup: current user is "me", a member of team "t". */
function setup(
  comments: Comment[],
  opts: { role?: 'admin' | 'member' | 'guest'; userId?: string } = {},
) {
  const role = opts.role ?? 'member'
  const userId = opts.userId ?? 'me'
  hooks.useComments.mockReturnValue({
    data: { items: comments, total: comments.length, page: 1, size: 50, pages: 1 },
    isLoading: false,
  })
  hooks.useCreateComment.mockReturnValue({ ...noopMutation })
  hooks.useUpdateComment.mockReturnValue({ ...noopMutation })
  hooks.useDeleteComment.mockReturnValue({ ...noopMutation })
  hooks.useUser.mockReturnValue({
    data: { id: userId, display_name: 'Ada', email: 'ada@x.com' },
  })
  hooks.useTeams.mockReturnValue({
    data: { items: [{ id: 't', key: 'ENG', my_role: role }] },
  })
}

describe('formatCommentTime', () => {
  it('returns — for invalid/blank timestamps (VAL-COMMENTS-004)', () => {
    expect(formatCommentTime(null)).toBe('—')
    expect(formatCommentTime('not-a-date')).toBe('—')
    expect(formatCommentTime(undefined)).toBe('—')
  })

  it('returns a relative label for recent timestamps', () => {
    const recent = new Date(Date.now() - 5 * 60 * 1000).toISOString() // 5m ago
    expect(formatCommentTime(recent)).toBe('5m ago')
  })
})

describe('CommentsThread', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows an empty state when there are no comments (VAL-COMMENTS-007)', () => {
    setup([])
    render(<CommentsThread issueId="issue-1" teamId="t" />)
    expect(screen.getByText(/start the discussion/i)).toBeInTheDocument()
  })

  it('renders comments newest-first with author + timestamp (VAL-COMMENTS-003/004)', () => {
    // Backend returns newest-first; the thread renders them in that order.
    const comments = [
      makeComment('c2', 'second', 'other', 'Bo'),
      makeComment('c1', 'first', 'me', 'Ada'),
    ]
    setup(comments)
    render(<CommentsThread issueId="issue-1" teamId="t" />)
    const bodies = screen.getAllByTestId('comment-body').map((el) => el.textContent)
    expect(bodies).toEqual(['second', 'first'])
    expect(screen.getByText('Bo')).toBeInTheDocument()
    expect(screen.getByText('Ada')).toBeInTheDocument()
  })

  it('blocks empty/whitespace submit (VAL-COMMENTS-002)', () => {
    setup([])
    render(<CommentsThread issueId="issue-1" teamId="t" />)
    const submit = screen.getByTestId('comment-submit')
    expect(submit).toBeDisabled()
    // Whitespace-only also blocked.
    fireEvent.change(screen.getByLabelText('Comment'), { target: { value: '   ' } })
    expect(submit).toBeDisabled()
  })

  it('creates a comment with the resolved author on submit (VAL-COMMENTS-001)', async () => {
    const mutateAsync = vi.fn().mockResolvedValue(undefined)
    hooks.useComments.mockReturnValue({ data: { items: [], total: 0, page: 1, size: 50, pages: 1 }, isLoading: false })
    hooks.useCreateComment.mockReturnValue({ ...noopMutation, mutateAsync })
    hooks.useUser.mockReturnValue({ data: { id: 'me', display_name: 'Ada', email: 'ada@x.com' } })
    hooks.useTeams.mockReturnValue({ data: { items: [{ id: 't', key: 'ENG', my_role: 'member' }] } })
    hooks.useUpdateComment.mockReturnValue({ ...noopMutation })
    hooks.useDeleteComment.mockReturnValue({ ...noopMutation })
    render(<CommentsThread issueId="issue-1" teamId="t" />)

    const textarea = screen.getByLabelText('Comment')
    fireEvent.change(textarea, { target: { value: 'Hello world' } })
    fireEvent.click(screen.getByTestId('comment-submit'))

    await waitFor(() =>
      expect(mutateAsync).toHaveBeenCalledWith({
        issue_id: 'issue-1',
        body: 'Hello world',
        author: { id: 'me', display_name: 'Ada', email: 'ada@x.com' },
      }),
    )
  })

  it('shows edit/delete controls to the author (VAL-COMMENTS-008)', () => {
    setup([makeComment('c1', 'mine', 'me', 'Ada')])
    render(<CommentsThread issueId="issue-1" teamId="t" />)
    expect(screen.getByTestId('comment-edit')).toBeInTheDocument()
    expect(screen.getByTestId('comment-delete')).toBeInTheDocument()
  })

  it('hides edit/delete controls from a non-author member (VAL-COMMENTS-008)', () => {
    // Current user is "me" (a member); the comment is authored by "other".
    setup([makeComment('c1', 'theirs', 'other', 'Bo')])
    render(<CommentsThread issueId="issue-1" teamId="t" />)
    expect(screen.queryByTestId('comment-edit')).not.toBeInTheDocument()
    expect(screen.queryByTestId('comment-delete')).not.toBeInTheDocument()
  })

  it('shows edit/delete controls to an admin even on others comments (VAL-COMMENTS-008)', () => {
    setup([makeComment('c1', 'theirs', 'other', 'Bo')], { role: 'admin' })
    render(<CommentsThread issueId="issue-1" teamId="t" />)
    expect(screen.getByTestId('comment-edit')).toBeInTheDocument()
    expect(screen.getByTestId('comment-delete')).toBeInTheDocument()
  })

  it('hides the composer for guests (read-only — VAL-COMMENTS-008)', () => {
    setup([], { role: 'guest' })
    render(<CommentsThread issueId="issue-1" teamId="t" />)
    expect(screen.queryByTestId('comment-composer')).not.toBeInTheDocument()
  })

  it('edits the body in place without duplicating (VAL-COMMENTS-005)', async () => {
    const mutateAsync = vi.fn().mockResolvedValue(undefined)
    hooks.useComments.mockReturnValue({
      data: { items: [makeComment('c1', 'old', 'me', 'Ada')], total: 1, page: 1, size: 50, pages: 1 },
      isLoading: false,
    })
    hooks.useCreateComment.mockReturnValue({ ...noopMutation })
    hooks.useUpdateComment.mockReturnValue({ ...noopMutation, mutateAsync })
    hooks.useDeleteComment.mockReturnValue({ ...noopMutation })
    hooks.useUser.mockReturnValue({ data: { id: 'me', display_name: 'Ada', email: 'ada@x.com' } })
    hooks.useTeams.mockReturnValue({ data: { items: [{ id: 't', key: 'ENG', my_role: 'member' }] } })
    render(<CommentsThread issueId="issue-1" teamId="t" />)

    fireEvent.click(screen.getByTestId('comment-edit'))
    const editBox = screen.getByLabelText('Edit comment')
    fireEvent.change(editBox, { target: { value: 'edited body' } })
    fireEvent.click(screen.getByText('Save'))

    await waitFor(() =>
      expect(mutateAsync).toHaveBeenCalledWith({ id: 'c1', body: 'edited body' }),
    )
  })

  it('deletes a comment after confirmation (VAL-COMMENTS-006)', async () => {
    const mutateAsync = vi.fn().mockResolvedValue(undefined)
    hooks.useComments.mockReturnValue({
      data: { items: [makeComment('c1', 'mine', 'me', 'Ada')], total: 1, page: 1, size: 50, pages: 1 },
      isLoading: false,
    })
    hooks.useCreateComment.mockReturnValue({ ...noopMutation })
    hooks.useUpdateComment.mockReturnValue({ ...noopMutation })
    hooks.useDeleteComment.mockReturnValue({ ...noopMutation, mutateAsync })
    hooks.useUser.mockReturnValue({ data: { id: 'me', display_name: 'Ada', email: 'ada@x.com' } })
    hooks.useTeams.mockReturnValue({ data: { items: [{ id: 't', key: 'ENG', my_role: 'member' }] } })
    render(<CommentsThread issueId="issue-1" teamId="t" />)

    // First click reveals the inline confirmation.
    fireEvent.click(screen.getByTestId('comment-delete'))
    const confirmAction = await screen.findByTestId('comment-delete-confirm-action')
    fireEvent.click(confirmAction)

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith({ id: 'c1' }))
  })
})
