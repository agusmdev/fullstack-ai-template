import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { SubIssuesPanel, computeSubIssueProgress } from './SubIssuesPanel'
import type { Issue } from '@/types/issue'
import type { WorkflowState } from '@/types/workflow-state'

// Mock the hooks used by SubIssuesPanel.
const hooks = vi.hoisted(() => ({
  useSubIssues: vi.fn(),
  useCreateIssue: vi.fn(),
  useUpdateIssue: vi.fn(),
  useTopLevelIssues: vi.fn(),
}))

vi.mock('@/hooks/useIssues', () => ({
  useSubIssues: hooks.useSubIssues,
  useCreateIssue: hooks.useCreateIssue,
  useUpdateIssue: hooks.useUpdateIssue,
  useTopLevelIssues: hooks.useTopLevelIssues,
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

function makeIssue(id: string, title: string, statusId: string, parentId: string | null = null): Issue {
  return {
    id,
    team_id: 't',
    identifier: `ENG-${id}`,
    title,
    description: null,
    status_id: statusId,
    priority: 4,
    assignee_id: null,
    creator_id: 'u',
    project_id: null,
    cycle_id: null,
    parent_id: parentId,
    sort_order: 0,
    estimate: null,
    due_date: null,
    labels: [],
    created_at: '',
    updated_at: '',
  }
}

describe('computeSubIssueProgress', () => {
  it('counts terminal-status children as done', () => {
    const children = [
      makeIssue('1', 'A', 's-backlog'),
      makeIssue('2', 'B', 's-done'),
      makeIssue('3', 'C', 's-done'),
    ]
    const result = computeSubIssueProgress(children, states)
    expect(result).toEqual({ total: 3, done: 2 })
  })

  it('returns zero for no children', () => {
    expect(computeSubIssueProgress([], states)).toEqual({ total: 0, done: 0 })
  })
})

describe('SubIssuesPanel', () => {
  beforeEach(() => {
    hooks.useSubIssues.mockReturnValue({ data: undefined, isLoading: false })
    hooks.useCreateIssue.mockReturnValue({ ...noopMutation })
    hooks.useUpdateIssue.mockReturnValue({ ...noopMutation })
    hooks.useTopLevelIssues.mockReturnValue({ data: undefined })
  })

  it('shows empty state when there are no sub-issues (VAL-SUBISSUES-006)', () => {
    hooks.useSubIssues.mockReturnValue({
      data: { items: [], total: 0, page: 1, size: 100, pages: 1 },
      isLoading: false,
    })
    render(<SubIssuesPanel issueId="parent" teamId="t" workflowStates={states} />)
    expect(screen.getByText('No sub-issues')).toBeInTheDocument()
  })

  it('renders children with identifier and title (VAL-SUBISSUES-001)', () => {
    const children = [
      makeIssue('1', 'First child', 's-backlog', 'parent'),
      makeIssue('2', 'Second child', 's-done', 'parent'),
    ]
    hooks.useSubIssues.mockReturnValue({
      data: { items: children, total: 2, page: 1, size: 100, pages: 1 },
      isLoading: false,
    })
    render(<SubIssuesPanel issueId="parent" teamId="t" workflowStates={states} />)
    expect(screen.getByText('First child')).toBeInTheDocument()
    expect(screen.getByText('Second child')).toBeInTheDocument()
    expect(screen.getByText('ENG-1')).toBeInTheDocument()
  })

  it('shows aggregate progress count (VAL-SUBISSUES-006)', () => {
    const children = [
      makeIssue('1', 'A', 's-backlog', 'parent'),
      makeIssue('2', 'B', 's-done', 'parent'),
    ]
    hooks.useSubIssues.mockReturnValue({
      data: { items: children, total: 2, page: 1, size: 100, pages: 1 },
      isLoading: false,
    })
    render(<SubIssuesPanel issueId="parent" teamId="t" workflowStates={states} />)
    // 1 of 2 done
    expect(screen.getByText('1/2')).toBeInTheDocument()
  })

  it('add sub-issue creates a child with parent_id set (VAL-SUBISSUES-001)', async () => {
    const mutateAsync = vi.fn().mockResolvedValue({})
    hooks.useCreateIssue.mockReturnValue({ ...noopMutation, mutateAsync })
    hooks.useSubIssues.mockReturnValue({
      data: { items: [], total: 0, page: 1, size: 100, pages: 1 },
      isLoading: false,
    })
    render(<SubIssuesPanel issueId="parent" teamId="t" workflowStates={states} />)

    fireEvent.click(screen.getByText('Add sub-issue'))
    const input = screen.getByPlaceholderText('Sub-issue title')
    fireEvent.change(input, { target: { value: 'New child' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    await waitFor(() =>
      expect(mutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          team_id: 't',
          title: 'New child',
          parent_id: 'parent',
        }),
      ),
    )
  })

  it('detach button clears parent_id via PATCH (VAL-SUBISSUES-005)', async () => {
    const mutate = vi.fn()
    hooks.useUpdateIssue.mockReturnValue({ ...noopMutation, mutate })
    const children = [makeIssue('1', 'Child', 's-backlog', 'parent')]
    hooks.useSubIssues.mockReturnValue({
      data: { items: children, total: 1, page: 1, size: 100, pages: 1 },
      isLoading: false,
    })
    render(<SubIssuesPanel issueId="parent" teamId="t" workflowStates={states} />)

    const detachBtn = screen.getByTitle('Remove from parent')
    fireEvent.click(detachBtn)

    await waitFor(() =>
      expect(mutate).toHaveBeenCalledWith({
        id: '1',
        team_id: 't',
        parent_id: null,
      }),
    )
  })

  it('clicking a child calls onSelectIssue (VAL-SUBISSUES-003)', () => {
    const onSelect = vi.fn()
    const children = [makeIssue('1', 'Child', 's-backlog', 'parent')]
    hooks.useSubIssues.mockReturnValue({
      data: { items: children, total: 1, page: 1, size: 100, pages: 1 },
      isLoading: false,
    })
    render(
      <SubIssuesPanel
        issueId="parent"
        teamId="t"
        workflowStates={states}
        onSelectIssue={onSelect}
      />,
    )

    fireEvent.click(screen.getByText('Child'))
    expect(onSelect).toHaveBeenCalledWith(
      expect.objectContaining({ id: '1' }),
    )
  })
})
