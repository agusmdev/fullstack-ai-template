import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { IssueFiltersBar } from './IssueFiltersBar'
import { DEFAULT_SORT_KEY } from '@/types/issue'
import type { WorkflowState } from '@/types/workflow-state'
import type { Label } from '@/types/label'

const states: WorkflowState[] = [
  { id: 's-backlog', team_id: 't', name: 'Backlog', type: 'backlog', position: 0, color: '#aaa' },
  { id: 's-progress', team_id: 't', name: 'In Progress', type: 'started', position: 2, color: '#ccc' },
]

const labels: Label[] = [
  { id: 'l-bug', team_id: 't', name: 'Bug', color: '#f00' },
  { id: 'l-ui', team_id: 't', name: 'UI', color: '#0f0' },
]

const members = [
  { id: 'u-1', name: 'Ada Lovelace' },
  { id: 'u-2', name: 'Grace Hopper' },
]

function renderBar(overrides: Partial<React.ComponentProps<typeof IssueFiltersBar>> = {}) {
  const onParamsChange = vi.fn()
  const onSearchInputChange = vi.fn()
  const onClear = vi.fn()
  const props: React.ComponentProps<typeof IssueFiltersBar> = {
    params: { sort: DEFAULT_SORT_KEY },
    searchInput: '',
    onSearchInputChange,
    onParamsChange,
    onClear,
    hasActive: false,
    workflowStates: states,
    labels,
    members,
    ...overrides,
  }
  return { ...render(<IssueFiltersBar {...props} />), onParamsChange, onSearchInputChange, onClear }
}

describe('IssueFiltersBar', () => {
  it('renders the search input and the four filter triggers', () => {
    renderBar()
    expect(screen.getByPlaceholderText('Filter by title…')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
    expect(screen.getByText('Priority')).toBeInTheDocument()
    expect(screen.getByText('Assignee')).toBeInTheDocument()
    expect(screen.getByText('Label')).toBeInTheDocument()
  })

  it('typing in search calls onSearchInputChange', () => {
    const { onSearchInputChange } = renderBar()
    fireEvent.change(screen.getByPlaceholderText('Filter by title…'), { target: { value: 'bug' } })
    expect(onSearchInputChange).toHaveBeenCalledWith('bug')
  })

  it('the clear-search button empties the input', () => {
    const { onSearchInputChange } = renderBar({ searchInput: 'bug' })
    fireEvent.click(screen.getByLabelText('Clear search'))
    expect(onSearchInputChange).toHaveBeenCalledWith('')
  })

  it('selecting a status filter calls onParamsChange with status_id', () => {
    const { onParamsChange } = renderBar()
    fireEvent.click(screen.getByText('Status'))
    fireEvent.click(screen.getByText('In Progress'))
    expect(onParamsChange).toHaveBeenCalledWith({ status_id: 's-progress' })
  })

  it('the "All statuses" item clears the status filter', () => {
    const { onParamsChange } = renderBar({ params: { status_id: 's-progress', sort: DEFAULT_SORT_KEY } })
    fireEvent.click(screen.getByText('In Progress'))
    fireEvent.click(screen.getByText('All statuses'))
    expect(onParamsChange).toHaveBeenCalledWith({ status_id: null })
  })

  it('selecting a priority filter calls onParamsChange with a numeric priority', () => {
    const { onParamsChange } = renderBar()
    fireEvent.click(screen.getByText('Priority'))
    fireEvent.click(screen.getByText('Urgent'))
    expect(onParamsChange).toHaveBeenCalledWith({ priority: 0 })
  })

  it('the assignee filter offers an Unassigned option and the known members', () => {
    const { onParamsChange } = renderBar()
    fireEvent.click(screen.getByText('Assignee'))
    // "Unassigned" + both members are offered while the menu is open.
    expect(screen.getByText('Unassigned')).toBeInTheDocument()
    expect(screen.getByText('Ada Lovelace')).toBeInTheDocument()
    expect(screen.getByText('Grace Hopper')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Unassigned'))
    expect(onParamsChange).toHaveBeenCalledWith({ assignee: 'unassigned' })
  })

  it('selecting a label filter calls onParamsChange with label_id', () => {
    const { onParamsChange } = renderBar()
    fireEvent.click(screen.getByText('Label'))
    fireEvent.click(screen.getByText('Bug'))
    expect(onParamsChange).toHaveBeenCalledWith({ label_id: 'l-bug' })
  })

  it('selecting a sort preset calls onParamsChange with the sort key', () => {
    const { onParamsChange } = renderBar()
    fireEvent.click(screen.getByText('Newest first'))
    // The sort menu is the only open menu containing the "Sort by" label.
    const sortMenu = screen.getByText('Sort by').parentElement!
    fireEvent.click(within(sortMenu).getByText('Priority'))
    expect(onParamsChange).toHaveBeenCalledWith({ sort: 'priority' })
  })

  it('shows the Clear button only when hasActive is true', () => {
    const { rerender } = renderBar({ hasActive: false })
    expect(screen.queryByRole('button', { name: /clear/i })).toBeNull()
    rerender(
      <IssueFiltersBar
        params={{ sort: DEFAULT_SORT_KEY }}
        searchInput=""
        onSearchInputChange={vi.fn()}
        onParamsChange={vi.fn()}
        onClear={vi.fn()}
        hasActive
        workflowStates={states}
        labels={labels}
        members={members}
      />,
    )
    expect(screen.getByRole('button', { name: /clear/i })).toBeInTheDocument()
  })

  it('the Clear button calls onClear', () => {
    const { onClear } = renderBar({ hasActive: true })
    fireEvent.click(screen.getByRole('button', { name: /clear/i }))
    expect(onClear).toHaveBeenCalledTimes(1)
  })
})
