import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ActivityFeed } from './ActivityFeed'
import { formatRelativeTime } from '@/lib/format-time'
import type { Activity, ActivityPayload } from '@/types/activity'

// Mock the hook so we control the rendered entries.
const hooks = vi.hoisted(() => ({ useActivity: vi.fn() }))
vi.mock('@/hooks/useActivity', () => ({ useActivity: hooks.useActivity }))

function makeActivity(
  id: string,
  type: Activity['type'],
  payload: ActivityPayload,
  actorName = 'Ada',
): Activity {
  return {
    id,
    issue_id: 'issue-1',
    actor_id: 'u1',
    type,
    payload,
    actor: { id: 'u1', display_name: actorName, email: 'ada@x.com' },
    created_at: '2024-01-01T00:00:00Z',
  }
}

/** Default setup: a list of entries (or loading/empty). */
function setup(entries: Activity[], isLoading = false) {
  hooks.useActivity.mockReturnValue({
    data: entries.length
      ? { items: entries, total: entries.length, page: 1, size: 50, pages: 1 }
      : undefined,
    isLoading,
  })
}

describe('formatRelativeTime', () => {
  it('returns — for invalid/blank timestamps', () => {
    expect(formatRelativeTime(null)).toBe('—')
    expect(formatRelativeTime('not-a-date')).toBe('—')
    expect(formatRelativeTime(undefined)).toBe('—')
  })

  it('returns a relative label for recent timestamps', () => {
    const recent = new Date(Date.now() - 5 * 60 * 1000).toISOString() // 5m ago
    expect(formatRelativeTime(recent)).toBe('5m ago')
  })
})

describe('ActivityFeed', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows an empty state when there is no activity', () => {
    setup([])
    render(<ActivityFeed issueId="issue-1" teamId="t" />)
    expect(screen.getByTestId('activity-empty')).toBeInTheDocument()
  })

  it('renders a loading state while fetching', () => {
    setup([], true)
    render(<ActivityFeed issueId="issue-1" teamId="t" />)
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('renders entries with actor + type + time (VAL-ACTIVITY-007)', () => {
    setup([
      makeActivity('a1', 'status_change', {
        from: { id: 's1', name: 'Backlog' },
        to: { id: 's2', name: 'In Progress' },
      }),
    ])
    render(<ActivityFeed issueId="issue-1" teamId="t" />)

    // Actor shown.
    expect(screen.getByText('Ada')).toBeInTheDocument()
    // Description carries from→to (VAL-ACTIVITY-001).
    const desc = screen.getByTestId('activity-description')
    expect(desc.textContent).toContain('Backlog')
    expect(desc.textContent).toContain('In Progress')
    // Time shown.
    expect(screen.getByTestId('activity-time')).toBeInTheDocument()
  })

  it('describes a status change from→to (VAL-ACTIVITY-001)', () => {
    setup([
      makeActivity('a1', 'status_change', {
        from: { id: 's1', name: 'Backlog' },
        to: { id: 's2', name: 'Done' },
      }),
    ])
    render(<ActivityFeed issueId="issue-1" teamId="t" />)
    expect(screen.getByTestId('activity-description').textContent).toContain(
      'changed status from Backlog to Done',
    )
  })

  it('describes an assignee change (VAL-ACTIVITY-002)', () => {
    setup([
      makeActivity('a1', 'assignee_change', { from: null, to: { id: 'u2', name: 'Bo' } }),
    ])
    render(<ActivityFeed issueId="issue-1" teamId="t" />)
    expect(screen.getByTestId('activity-description').textContent).toContain(
      'assigned to Bo',
    )
  })

  it('describes a priority change (VAL-ACTIVITY-003)', () => {
    setup([makeActivity('a1', 'priority_change', { from: 4, to: 0 })])
    render(<ActivityFeed issueId="issue-1" teamId="t" />)
    const text = screen.getByTestId('activity-description').textContent ?? ''
    expect(text).toContain('No priority')
    expect(text).toContain('Urgent')
  })

  it('describes a title rename (VAL-ACTIVITY-004)', () => {
    setup([makeActivity('a1', 'title_rename', { from: 'Old', to: 'New' })])
    render(<ActivityFeed issueId="issue-1" teamId="t" />)
    expect(screen.getByTestId('activity-description').textContent).toContain(
      'renamed the issue',
    )
  })

  it('describes a label added (VAL-ACTIVITY-005)', () => {
    setup([
      makeActivity('a1', 'label_added', { label: { id: 'l1', name: 'Bug' } }),
    ])
    render(<ActivityFeed issueId="issue-1" teamId="t" />)
    expect(screen.getByTestId('activity-description').textContent).toContain(
      'added the Bug label',
    )
  })

  it('describes a label removed (VAL-ACTIVITY-006)', () => {
    setup([
      makeActivity('a1', 'label_removed', { label: { id: 'l1', name: 'Bug' } }),
    ])
    render(<ActivityFeed issueId="issue-1" teamId="t" />)
    expect(screen.getByTestId('activity-description').textContent).toContain(
      'removed the Bug label',
    )
  })

  it('renders entries newest-first as returned by the backend', () => {
    setup([
      makeActivity('a2', 'priority_change', { from: 4, to: 0 }, 'Bo'),
      makeActivity('a1', 'status_change', {
        from: { id: 's1', name: 'Backlog' },
        to: { id: 's2', name: 'Todo' },
      }),
    ])
    render(<ActivityFeed issueId="issue-1" teamId="t" />)
    const actors = screen.getAllByTestId('activity-actor').map((el) => el.textContent)
    expect(actors).toEqual(['Bo', 'Ada'])
  })

  it('is read-only — no composer/input exists (VAL-ACTIVITY-009)', () => {
    setup([makeActivity('a1', 'status_change', { from: { id: 's', name: 'A' }, to: { id: 's2', name: 'B' } })])
    const { container } = render(<ActivityFeed issueId="issue-1" teamId="t" />)
    expect(container.querySelector('textarea')).toBeNull()
    expect(container.querySelector('input')).toBeNull()
    expect(screen.queryByRole('button', { name: /comment|submit|add/i })).toBeNull()
  })
})
