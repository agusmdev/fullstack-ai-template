import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { IssueDetailDrawer } from './IssueDetailDrawer'
import type { Issue } from '@/types/issue'
import type { WorkflowState } from '@/types/workflow-state'
import type { Label } from '@/types/label'

// Mock all hooks used by the drawer so the test is deterministic and isolated.
const hooks = vi.hoisted(() => ({
  useIssue: vi.fn(),
  useUpdateIssue: vi.fn(),
  useDeleteIssue: vi.fn(),
  useAddIssueLabel: vi.fn(),
  useRemoveIssueLabel: vi.fn(),
}))

vi.mock('@/hooks/useIssues', () => ({
  useIssue: hooks.useIssue,
  useUpdateIssue: hooks.useUpdateIssue,
  useDeleteIssue: hooks.useDeleteIssue,
  useAddIssueLabel: hooks.useAddIssueLabel,
  useRemoveIssueLabel: hooks.useRemoveIssueLabel,
}))

const noopMutation = {
  mutate: vi.fn(),
  mutateAsync: vi.fn(),
  isPending: false,
  isSuccess: false,
  isError: false,
}

const states: WorkflowState[] = [
  { id: 's-backlog', team_id: 't', name: 'Backlog', type: 'backlog', position: 0, color: '#aaa' },
  { id: 's-todo', team_id: 't', name: 'Todo', type: 'unstarted', position: 1, color: '#bbb' },
  { id: 's-done', team_id: 't', name: 'Done', type: 'completed', position: 3, color: '#ddd' },
]

const labels: Label[] = [{ id: 'l-1', team_id: 't', name: 'Bug', color: '#f00' }]

const issue: Issue = {
  id: 'i-1',
  team_id: 't',
  identifier: 'ENG-1',
  title: 'Fix the bug',
  description: 'Step one\nStep two',
  status_id: 's-backlog',
  priority: 2,
  assignee_id: null,
  creator_id: 'u-1',
  project_id: null,
  cycle_id: null,
  parent_id: null,
  sort_order: 0,
  estimate: null,
  due_date: null,
  labels: [{ id: 'l-1', name: 'Bug', color: '#f00' }],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-02T00:00:00Z',
}

function renderDrawer(overrides: Partial<React.ComponentProps<typeof IssueDetailDrawer>> = {}) {
  return render(
    <IssueDetailDrawer
      open
      onOpenChange={vi.fn()}
      issueId="i-1"
      initialIssue={issue}
      teamId="t"
      workflowStates={states}
      labels={labels}
      members={[{ id: 'u-1', name: 'Ada Lovelace' }]}
      {...overrides}
    />,
  )
}

describe('IssueDetailDrawer', () => {
  beforeEach(() => {
    hooks.useIssue.mockReturnValue({ data: issue, isLoading: false })
    hooks.useUpdateIssue.mockReturnValue({ ...noopMutation })
    hooks.useDeleteIssue.mockReturnValue({ ...noopMutation })
    hooks.useAddIssueLabel.mockReturnValue({ ...noopMutation })
    hooks.useRemoveIssueLabel.mockReturnValue({ ...noopMutation })
  })

  it('renders complete correct data on open (VAL-ISSUES-030)', () => {
    renderDrawer()
    expect(screen.getByText('ENG-1')).toBeInTheDocument()
    expect(screen.getByText('Fix the bug')).toBeInTheDocument()
    // Description (multiline) is preserved verbatim (VAL-ISSUES-032).
    const desc = screen.getByTestId('issue-description')
    expect(desc.textContent).toBe('Step one\nStep two')
    // Label badge
    expect(screen.getAllByText('Bug').length).toBeGreaterThan(0)
    // Status shown
    expect(screen.getByText('Backlog')).toBeInTheDocument()
    // Timestamps rendered (not Invalid Date)
    expect(screen.getByText(/Created/)).toBeInTheDocument()
  })

  it('shows a skeleton while the issue GET is in flight (VAL-ISSUES-048)', () => {
    hooks.useIssue.mockReturnValue({ data: undefined, isLoading: true })
    renderDrawer()
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.getByText('Loading issue…')).toBeInTheDocument()
    // The title/description are not rendered during loading.
    expect(screen.queryByText('Fix the bug')).not.toBeInTheDocument()
  })

  it('inline title edit commits via PATCH on Enter (VAL-ISSUES-031)', async () => {
    const mutate = vi.fn()
    hooks.useUpdateIssue.mockReturnValue({ ...noopMutation, mutate })
    renderDrawer()

    // Click the title to enter edit mode.
    fireEvent.click(screen.getByText('Fix the bug'))
    const input = await screen.findByDisplayValue('Fix the bug')
    fireEvent.change(input, { target: { value: 'Renamed title' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    await waitFor(() =>
      expect(mutate).toHaveBeenCalledWith({ id: 'i-1', team_id: 't', title: 'Renamed title' }),
    )
  })

  it('does not PATCH when the title is unchanged', async () => {
    const mutate = vi.fn()
    hooks.useUpdateIssue.mockReturnValue({ ...noopMutation, mutate })
    renderDrawer()
    fireEvent.click(screen.getByText('Fix the bug'))
    const input = await screen.findByDisplayValue('Fix the bug')
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(mutate).not.toHaveBeenCalled()
  })

  it('description edit commits on Save (VAL-ISSUES-032)', async () => {
    const mutate = vi.fn()
    hooks.useUpdateIssue.mockReturnValue({ ...noopMutation, mutate })
    renderDrawer()
    fireEvent.click(screen.getByTestId('issue-description'))
    const textarea = await screen.findByRole('textbox', { name: 'Issue description' })
    expect((textarea as HTMLTextAreaElement).value).toBe('Step one\nStep two')
    fireEvent.change(textarea, { target: { value: 'New body' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() =>
      expect(mutate).toHaveBeenCalledWith({ id: 'i-1', team_id: 't', description: 'New body' }),
    )
  })

  it('status change calls PATCH with the new status_id (VAL-ISSUES-033)', async () => {
    const mutate = vi.fn()
    hooks.useUpdateIssue.mockReturnValue({ ...noopMutation, mutate })
    renderDrawer()
    // Open the status picker (the Backlog button) and pick Done.
    fireEvent.click(screen.getByText('Backlog'))
    fireEvent.click(screen.getByText('Done'))
    await waitFor(() =>
      expect(mutate).toHaveBeenCalledWith({ id: 'i-1', team_id: 't', status_id: 's-done' }),
    )
  })

  it('delete shows a confirm guard before deleting (VAL-ISSUES-039, 038)', async () => {
    const mutate = vi.fn()
    hooks.useDeleteIssue.mockReturnValue({ ...noopMutation, mutate })
    renderDrawer()
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    // Confirm dialog appears.
    expect(await screen.findByText('Delete issue?')).toBeInTheDocument()
    // Cancel leaves the issue (no delete).
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(mutate).not.toHaveBeenCalled()
  })

  it('confirming delete fires the DELETE mutation (VAL-ISSUES-038)', async () => {
    // Simulate success so the onSuccess callback runs.
    hooks.useDeleteIssue.mockReturnValue({
      ...noopMutation,
      mutate: (_vars: { id: string; team_id: string }, opts?: { onSuccess?: () => void }) => {
        opts?.onSuccess?.()
      },
    })
    const onOpenChange = vi.fn()
    renderDrawer({ onOpenChange })
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    fireEvent.click(await screen.findByRole('button', { name: 'Delete issue' }))
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false))
  })

  it('renders a terminal issue with strikethrough styling (VAL-ISSUES-044)', () => {
    hooks.useIssue.mockReturnValue({
      data: { ...issue, status_id: 's-done' },
      isLoading: false,
    })
    renderDrawer()
    const title = screen.getByText('Fix the bug')
    expect(title.className).toContain('line-through')
  })
})
