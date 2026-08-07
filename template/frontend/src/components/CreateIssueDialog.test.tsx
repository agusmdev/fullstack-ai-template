import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { CreateIssueDialog } from './CreateIssueDialog'
import { ISSUE_TITLE_MAX } from '@/features/issues/issue-schemas'
import type { CreateIssueInput } from '@/types/issue'
import type { WorkflowState } from '@/types/workflow-state'
import type { Label } from '@/types/label'

const createMock = vi.hoisted(() => ({
  mutateAsync: vi.fn(),
  isPending: false,
}))

vi.mock('@/hooks/useIssues', () => ({
  useCreateIssue: () => createMock,
}))

const states: WorkflowState[] = [
  { id: 's-backlog', team_id: 't', name: 'Backlog', type: 'backlog', position: 0, color: '#aaa' },
  { id: 's-todo', team_id: 't', name: 'Todo', type: 'unstarted', position: 1, color: '#bbb' },
  { id: 's-progress', team_id: 't', name: 'In Progress', type: 'started', position: 2, color: '#ccc' },
  { id: 's-done', team_id: 't', name: 'Done', type: 'completed', position: 3, color: '#ddd' },
  { id: 's-canceled', team_id: 't', name: 'Canceled', type: 'canceled', position: 4, color: '#eee' },
]

const labels: Label[] = [
  { id: 'l-1', team_id: 't', name: 'Bug', color: '#f00' },
  { id: 'l-2', team_id: 't', name: 'Feature', color: '#0f0' },
]

function typeValue(el: HTMLElement, value: string) {
  fireEvent.change(el, { target: { value } })
  fireEvent.blur(el)
}

function renderDialog(overrides: Partial<React.ComponentProps<typeof CreateIssueDialog>> = {}) {
  const onOpenChange = vi.fn()
  const utils = render(
    <CreateIssueDialog
      open
      onOpenChange={onOpenChange}
      teamId="t-1"
      workflowStates={states}
      labels={labels}
      members={[{ id: 'u-1', name: 'Ada Lovelace' }]}
      {...overrides}
    />,
  )
  return { ...utils, onOpenChange }
}

describe('CreateIssueDialog', () => {
  beforeEach(() => {
    createMock.mutateAsync.mockReset()
    createMock.mutateAsync.mockResolvedValue({})
    createMock.isPending = false
  })

  it('opens with blank title/description and documented defaults (VAL-ISSUES-001, 005)', () => {
    renderDialog()
    const titleInput = screen.getByPlaceholderText('Issue title') as HTMLInputElement
    expect(titleInput.value).toBe('')
    expect((screen.getByPlaceholderText('Add description…') as HTMLTextAreaElement).value).toBe('')
    // Default status = first workflow state (Backlog)
    expect(screen.getByText('Backlog')).toBeInTheDocument()
    // Default priority = No priority
    expect(screen.getByText('No priority')).toBeInTheDocument()
    // Default assignee = Unassigned
    expect(screen.getByText('Unassigned')).toBeInTheDocument()
    // Default labels = none (shows "Labels")
    expect(screen.getByText('Labels')).toBeInTheDocument()
  })

  it('disables submit while title is empty (VAL-ISSUES-002)', () => {
    renderDialog()
    expect(screen.getByRole('button', { name: /create issue/i })).toBeDisabled()
  })

  it('rejects whitespace-only title (VAL-ISSUES-003)', async () => {
    renderDialog()
    typeValue(screen.getByPlaceholderText('Issue title'), '   ')
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /create issue/i })).toBeDisabled()
    })
  })

  it('enables submit for a valid single-char title (VAL-ISSUES-004)', async () => {
    renderDialog()
    typeValue(screen.getByPlaceholderText('Issue title'), 'X')
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /create issue/i })).toBeEnabled()
    })
  })

  it('enforces the title maxLength on the input (VAL-ISSUES-004)', () => {
    renderDialog()
    const titleInput = screen.getByPlaceholderText('Issue title') as HTMLInputElement
    // The browser clamps typed/pasted text at maxLength; the attribute is the guard.
    expect(titleInput.maxLength).toBe(ISSUE_TITLE_MAX)
  })

  it('creates with title-only applying defaults and closes (VAL-ISSUES-005, 010)', async () => {
    const { onOpenChange } = renderDialog()
    typeValue(screen.getByPlaceholderText('Issue title'), 'My issue')
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /create issue/i })).toBeEnabled(),
    )
    fireEvent.click(screen.getByRole('button', { name: /create issue/i }))

    await waitFor(() => expect(createMock.mutateAsync).toHaveBeenCalledTimes(1))
    const payload = createMock.mutateAsync.mock.calls[0][0] as CreateIssueInput
    expect(payload.title).toBe('My issue')
    expect(payload.status_id).toBe('s-backlog') // first workflow state
    expect(payload.priority).toBe(4) // No priority
    expect(payload.assignee_id).toBeNull()
    expect(payload.label_ids).toBeUndefined()
    // Dialog closes on success.
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false))
  })

  it('keeps the dialog open on backend error (VAL-ISSUES-009)', async () => {
    createMock.mutateAsync.mockRejectedValue(new Error('boom'))
    const { onOpenChange } = renderDialog()
    typeValue(screen.getByPlaceholderText('Issue title'), 'Keep me')
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /create issue/i })).toBeEnabled(),
    )
    fireEvent.click(screen.getByRole('button', { name: /create issue/i }))

    await waitFor(() => expect(createMock.mutateAsync).toHaveBeenCalled())
    // Input is preserved and the dialog was NOT closed.
    expect((screen.getByPlaceholderText('Issue title') as HTMLInputElement).value).toBe('Keep me')
    expect(onOpenChange).not.toHaveBeenCalled()
  })

  it('persists a multiline description (VAL-ISSUES-007)', async () => {
    renderDialog()
    typeValue(screen.getByPlaceholderText('Issue title'), 'T')
    typeValue(
      screen.getByPlaceholderText('Add description…') as HTMLTextAreaElement,
      'Line one\nLine two',
    )
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /create issue/i })).toBeEnabled(),
    )
    fireEvent.click(screen.getByRole('button', { name: /create issue/i }))

    await waitFor(() => expect(createMock.mutateAsync).toHaveBeenCalled())
    const payload = createMock.mutateAsync.mock.calls[0][0] as CreateIssueInput
    expect(payload.description).toBe('Line one\nLine two')
  })

  it('does not fire the API on submit with an empty title (VAL-ISSUES-002)', () => {
    renderDialog()
    const form = screen.getByPlaceholderText('Issue title').closest('form')!
    fireEvent.submit(form)
    expect(createMock.mutateAsync).not.toHaveBeenCalled()
  })
})
