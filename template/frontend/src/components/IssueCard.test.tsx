import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { IssueCard } from './IssueCard'
import type { Issue } from '@/types/issue'

function makeIssue(overrides: Partial<Issue> = {}): Issue {
  return {
    id: 'i-1',
    team_id: 't',
    identifier: 'ENG-1',
    title: 'Fix login bug',
    description: null,
    status_id: 's-todo',
    priority: 0,
    assignee_id: 'u-1',
    creator_id: 'u-1',
    project_id: null,
    cycle_id: null,
    parent_id: null,
    sort_order: 0,
    estimate: null,
    due_date: null,
    labels: [],
    created_at: '',
    updated_at: '',
    ...overrides,
  }
}

describe('IssueCard', () => {
  it('renders identifier, title, priority, and assignee', () => {
    render(
      <IssueCard issue={makeIssue()} assigneeName="Alice Smith" />,
    )
    expect(screen.getByText('ENG-1')).toBeInTheDocument()
    expect(screen.getByText('Fix login bug')).toBeInTheDocument()
    expect(screen.getByText('AS')).toBeInTheDocument() // initials
  })

  it('renders label badges', () => {
    const issue = makeIssue({
      labels: [
        { id: 'l1', name: 'bug', color: '#f00' },
        { id: 'l2', name: 'urgent', color: null },
      ],
    })
    render(<IssueCard issue={issue} />)
    expect(screen.getByText('bug')).toBeInTheDocument()
    expect(screen.getByText('urgent')).toBeInTheDocument()
  })

  it('renders an unassigned avatar placeholder when no assignee', () => {
    render(<IssueCard issue={makeIssue({ assignee_id: null })} />)
    // The UserRound icon is rendered for unassigned
    expect(screen.queryByText('AS')).not.toBeInTheDocument()
  })

  /** Helper: find the card root element (the draggable div). */
  function getCard() {
    return screen.getByText('Fix login bug').closest('[aria-label]')!
  }

  it('is draggable by default', () => {
    render(<IssueCard issue={makeIssue()} />)
    expect(getCard()).toHaveAttribute('draggable', 'true')
  })

  it('is NOT draggable when optimistic', () => {
    render(<IssueCard issue={makeIssue({ id: 'optimistic-xyz' })} />)
    expect(getCard()).toHaveAttribute('draggable', 'false')
  })

  it('sets the issue id in dataTransfer on dragStart', () => {
    const onDragStart = vi.fn()
    render(<IssueCard issue={makeIssue()} onDragStart={onDragStart} />)

    const dt = { setData: vi.fn(), effectAllowed: '' }
    fireEvent.dragStart(getCard(), { dataTransfer: dt })

    expect(dt.setData).toHaveBeenCalledWith('text/plain', 'i-1')
    expect(dt.effectAllowed).toBe('move')
    expect(onDragStart).toHaveBeenCalledOnce()
  })

  it('calls onDragEnd when the drag ends', () => {
    const onDragEnd = vi.fn()
    render(<IssueCard issue={makeIssue()} onDragEnd={onDragEnd} />)
    fireEvent.dragEnd(getCard())
    expect(onDragEnd).toHaveBeenCalledOnce()
  })

  it('calls onSelect when clicked', () => {
    const onSelect = vi.fn()
    render(<IssueCard issue={makeIssue()} onSelect={onSelect} />)
    fireEvent.click(screen.getByRole('button'))
    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: 'i-1' }))
  })

  it('calls onSelect on Enter key', () => {
    const onSelect = vi.fn()
    render(<IssueCard issue={makeIssue()} onSelect={onSelect} />)
    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' })
    expect(onSelect).toHaveBeenCalledOnce()
  })

  it('applies strikethrough for terminal status', () => {
    render(<IssueCard issue={makeIssue()} isTerminal />)
    const title = screen.getByText('Fix login bug')
    expect(title.className).toContain('line-through')
  })

  it('renders placeholder identifier for optimistic rows', () => {
    render(<IssueCard issue={makeIssue({ id: 'optimistic-1', identifier: '' })} />)
    expect(screen.getByText('···')).toBeInTheDocument()
  })
})
