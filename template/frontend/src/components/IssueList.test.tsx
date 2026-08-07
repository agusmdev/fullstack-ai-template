import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { IssueList, groupIssuesByStatus } from './IssueList'
import type { Issue } from '@/types/issue'
import type { WorkflowState } from '@/types/workflow-state'

const states: WorkflowState[] = [
  { id: 's-backlog', team_id: 't', name: 'Backlog', type: 'backlog', position: 0, color: '#aaa' },
  { id: 's-todo', team_id: 't', name: 'Todo', type: 'unstarted', position: 1, color: '#bbb' },
  { id: 's-progress', team_id: 't', name: 'In Progress', type: 'started', position: 2, color: '#ccc' },
  { id: 's-done', team_id: 't', name: 'Done', type: 'completed', position: 3, color: '#ddd' },
  { id: 's-canceled', team_id: 't', name: 'Canceled', type: 'canceled', position: 4, color: '#eee' },
]

function makeIssue(id: string, statusId: string, title: string, identifier: string, parentId: string | null = null): Issue {
  return {
    id,
    team_id: 't',
    identifier,
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

describe('groupIssuesByStatus', () => {
  it('groups issues in canonical workflow order by position', () => {
    // Issues intentionally given out of order to prove grouping reorders them.
    const issues = [
      makeIssue('1', 's-done', 'D', 'T-3'),
      makeIssue('2', 's-backlog', 'A', 'T-1'),
      makeIssue('3', 's-progress', 'C', 'T-2'),
    ]
    const groups = groupIssuesByStatus(issues, states)
    expect(groups.map((g) => g.state.name)).toEqual([
      'Backlog',
      'Todo',
      'In Progress',
      'Done',
      'Canceled',
    ])
    expect(groups[0].issues.map((i) => i.title)).toEqual(['A'])
    expect(groups[2].issues.map((i) => i.title)).toEqual(['C'])
  })

  it('includes empty groups with count 0', () => {
    const issues = [makeIssue('1', 's-backlog', 'A', 'T-1')]
    const groups = groupIssuesByStatus(issues, states)
    const todo = groups.find((g) => g.state.name === 'Todo')!
    expect(todo.issues).toHaveLength(0)
  })

  it('reports accurate per-group counts', () => {
    const issues = [
      makeIssue('1', 's-backlog', 'A', 'T-1'),
      makeIssue('2', 's-backlog', 'B', 'T-2'),
      makeIssue('3', 's-progress', 'C', 'T-3'),
    ]
    const groups = groupIssuesByStatus(issues, states)
    const backlog = groups.find((g) => g.state.name === 'Backlog')!
    const progress = groups.find((g) => g.state.name === 'In Progress')!
    expect(backlog.issues).toHaveLength(2)
    expect(progress.issues).toHaveLength(1)
  })

  it('includes all issues in status groups (board uses this)', () => {
    const issues = [
      makeIssue('parent', 's-backlog', 'Parent', 'T-1'),
      makeIssue('child', 's-progress', 'Child', 'T-2', 'parent'),
    ]
    const groups = groupIssuesByStatus(issues, states)
    const backlog = groups.find((g) => g.state.name === 'Backlog')!
    const progress = groups.find((g) => g.state.name === 'In Progress')!
    // Both parent and child are grouped by their own status (board behavior).
    expect(backlog.issues.map((i) => i.id)).toEqual(['parent'])
    expect(progress.issues.map((i) => i.id)).toEqual(['child'])
  })
})

describe('IssueList', () => {
  it('renders group headers with accurate counts', () => {
    const issues = [
      makeIssue('1', 's-backlog', 'First', 'T-1'),
      makeIssue('2', 's-backlog', 'Second', 'T-2'),
      makeIssue('3', 's-progress', 'Third', 'T-3'),
    ]
    render(<IssueList issues={issues} workflowStates={states} />)

    expect(screen.getByText('Backlog')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('In Progress')).toBeInTheDocument()
    expect(screen.getByText('First')).toBeInTheDocument()
    expect(screen.getByText('Third')).toBeInTheDocument()
  })

  it('shows a zero count and "No issues" for an empty group', () => {
    const issues = [makeIssue('1', 's-backlog', 'Only', 'T-1')]
    render(<IssueList issues={issues} workflowStates={states} />)

    expect(screen.getByText('Todo')).toBeInTheDocument()
    // The four empty groups (Todo, In Progress, Done, Canceled) each show the placeholder.
    expect(screen.getAllByText('No issues')).toHaveLength(4)
  })

  it('renders the issue identifier', () => {
    const issues = [makeIssue('1', 's-backlog', 'First', 'ENG-1')]
    render(<IssueList issues={issues} workflowStates={states} />)
    expect(screen.getByText('ENG-1')).toBeInTheDocument()
  })

  it('renders children nested under their parent (VAL-SUBISSUES-002)', () => {
    const issues = [
      makeIssue('parent', 's-backlog', 'Parent issue', 'T-1'),
      makeIssue('child1', 's-progress', 'Child one', 'T-2', 'parent'),
      makeIssue('child2', 's-done', 'Child two', 'T-3', 'parent'),
    ]
    render(<IssueList issues={issues} workflowStates={states} />)

    // The parent and both children should all be visible (expanded by default).
    expect(screen.getByText('Parent issue')).toBeInTheDocument()
    expect(screen.getByText('Child one')).toBeInTheDocument()
    expect(screen.getByText('Child two')).toBeInTheDocument()
    // The child count badge shows "2".
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('collapse toggle hides children (VAL-SUBISSUES-002)', () => {
    const issues = [
      makeIssue('parent', 's-backlog', 'Parent issue', 'T-1'),
      makeIssue('child1', 's-progress', 'Child one', 'T-2', 'parent'),
    ]
    render(<IssueList issues={issues} workflowStates={states} />)

    // Children visible by default.
    expect(screen.getByText('Child one')).toBeInTheDocument()

    // Click the collapse toggle.
    const toggle = screen.getByLabelText('Collapse sub-issues')
    fireEvent.click(toggle)

    // Child is now hidden.
    expect(screen.queryByText('Child one')).not.toBeInTheDocument()
    // The expand toggle is now available.
    expect(screen.getByLabelText('Expand sub-issues')).toBeInTheDocument()
  })

  it('onSelectIssue fires for both parent and child rows', () => {
    const onSelect = vi.fn()
    const issues = [
      makeIssue('parent', 's-backlog', 'Parent issue', 'T-1'),
      makeIssue('child', 's-progress', 'Child issue', 'T-2', 'parent'),
    ]
    render(<IssueList issues={issues} workflowStates={states} onSelectIssue={onSelect} />)

    fireEvent.click(screen.getByText('Child issue'))
    expect(onSelect).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'child' }),
    )
  })
})
