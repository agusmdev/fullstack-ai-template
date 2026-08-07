import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { DependenciesPanel } from './DependenciesPanel'
import type { IssueDependency } from '@/types/issue-dependency'
import type { WorkflowState } from '@/types/workflow-state'

// Mock the hooks used by DependenciesPanel.
const hooks = vi.hoisted(() => ({
  useIssueDependencies: vi.fn(),
  useCreateIssueDependency: vi.fn(),
  useDeleteIssueDependency: vi.fn(),
  useTeamIssuesForPicker: vi.fn(),
}))

vi.mock('@/hooks/useIssueDependencies', () => ({
  useIssueDependencies: hooks.useIssueDependencies,
  useCreateIssueDependency: hooks.useCreateIssueDependency,
  useDeleteIssueDependency: hooks.useDeleteIssueDependency,
  useTeamIssuesForPicker: hooks.useTeamIssuesForPicker,
  splitDependencies: (
    deps: IssueDependency[],
    issueId: string,
  ) => {
    const blocking = deps.filter((d) => d.blocker_id === issueId)
    const blockedBy = deps.filter((d) => d.blocked_id === issueId)
    return { blocking, blockedBy }
  },
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

function makeDep(
  id: string,
  blockerId: string,
  blockedId: string,
  blockerIdent = 'ENG-1',
  blockedIdent = 'ENG-2',
): IssueDependency {
  return {
    id,
    blocker_id: blockerId,
    blocked_id: blockedId,
    relation: 'blocks',
    blocker: {
      id: blockerId,
      identifier: blockerId === 'current' ? 'CUR-1' : blockerIdent,
      title: blockerId === 'current' ? 'Current' : 'Blocker issue',
      priority: 2,
      status_id: 's-backlog',
    },
    blocked: {
      id: blockedId,
      identifier: blockedId === 'current' ? 'CUR-1' : blockedIdent,
      title: blockedId === 'current' ? 'Current' : 'Blocked issue',
      priority: 3,
      status_id: 's-backlog',
    },
    created_at: '',
    updated_at: '',
  }
}

describe('DependenciesPanel', () => {
  beforeEach(() => {
    hooks.useIssueDependencies.mockReturnValue({
      data: undefined,
      isLoading: false,
    })
    hooks.useCreateIssueDependency.mockReturnValue({ ...noopMutation })
    hooks.useDeleteIssueDependency.mockReturnValue({ ...noopMutation })
    hooks.useTeamIssuesForPicker.mockReturnValue({ data: undefined })
  })

  it('shows the section header with a count (VAL-DEPS-002)', () => {
    hooks.useIssueDependencies.mockReturnValue({
      data: { items: [makeDep('d1', 'current', 'b')], total: 1, page: 1, size: 100, pages: 1 },
      isLoading: false,
    })
    render(<DependenciesPanel issueId="current" teamId="t" workflowStates={states} />)
    expect(screen.getByText('Dependencies')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
  })

  it('renders reciprocal "Blocking" and "Blocked by" sections (VAL-DEPS-002)', () => {
    // current blocks b  →  b appears under "Blocking"
    hooks.useIssueDependencies.mockReturnValue({
      data: { items: [makeDep('d1', 'current', 'b', 'CUR-1', 'ENG-9')], total: 1, page: 1, size: 100, pages: 1 },
      isLoading: false,
    })
    render(<DependenciesPanel issueId="current" teamId="t" workflowStates={states} />)
    expect(screen.getByText('Blocking')).toBeInTheDocument()
    expect(screen.getByText('Blocked issue')).toBeInTheDocument()
    expect(screen.getByText('ENG-9')).toBeInTheDocument()
  })

  it('shows a related issue under "Blocked by" when another issue blocks it (VAL-DEPS-002)', () => {
    // a blocks current  →  a appears under "Blocked by"
    hooks.useIssueDependencies.mockReturnValue({
      data: { items: [makeDep('d1', 'a', 'current', 'ENG-7', 'CUR-1')], total: 1, page: 1, size: 100, pages: 1 },
      isLoading: false,
    })
    render(<DependenciesPanel issueId="current" teamId="t" workflowStates={states} />)
    expect(screen.getByText('Blocked by')).toBeInTheDocument()
    expect(screen.getByText('Blocker issue')).toBeInTheDocument()
    expect(screen.getByText('ENG-7')).toBeInTheDocument()
  })

  it('delete button removes the dependency (VAL-DEPS-004)', async () => {
    const mutate = vi.fn()
    hooks.useDeleteIssueDependency.mockReturnValue({ ...noopMutation, mutate })
    hooks.useIssueDependencies.mockReturnValue({
      data: { items: [makeDep('d1', 'current', 'b', 'CUR-1', 'ENG-9')], total: 1, page: 1, size: 100, pages: 1 },
      isLoading: false,
    })
    render(<DependenciesPanel issueId="current" teamId="t" workflowStates={states} />)

    fireEvent.click(screen.getByTitle('Remove dependency'))
    await waitFor(() =>
      expect(mutate).toHaveBeenCalledWith({ id: 'd1', team_id: 't' }),
    )
  })

  it('add blocking creates a dependency where current blocks the picked issue (VAL-DEPS-001)', async () => {
    const mutate = vi.fn()
    hooks.useCreateIssueDependency.mockReturnValue({ ...noopMutation, mutate })
    hooks.useIssueDependencies.mockReturnValue({
      data: { items: [], total: 0, page: 1, size: 100, pages: 1 },
      isLoading: false,
    })
    hooks.useTeamIssuesForPicker.mockReturnValue({
      data: {
        items: [
          { id: 'b', team_id: 't', identifier: 'ENG-9', title: 'Other issue', status_id: 's-backlog', priority: 3 } as never,
        ],
        total: 1,
      },
    })
    render(<DependenciesPanel issueId="current" teamId="t" workflowStates={states} />)

    fireEvent.click(screen.getByText('Add blocking'))
    // Candidate button rendered as "ENG-9 — Other issue"
    fireEvent.click(screen.getByText('Other issue'))

    await waitFor(() =>
      expect(mutate).toHaveBeenCalledWith({
        blocker_id: 'current',
        blocked_id: 'b',
        team_id: 't',
      }),
    )
  })

  it('add blocked by creates a dependency where the picked issue blocks current', async () => {
    const mutate = vi.fn()
    hooks.useCreateIssueDependency.mockReturnValue({ ...noopMutation, mutate })
    hooks.useIssueDependencies.mockReturnValue({
      data: { items: [], total: 0, page: 1, size: 100, pages: 1 },
      isLoading: false,
    })
    hooks.useTeamIssuesForPicker.mockReturnValue({
      data: {
        items: [
          { id: 'a', team_id: 't', identifier: 'ENG-7', title: 'Other issue', status_id: 's-backlog', priority: 2 } as never,
        ],
        total: 1,
      },
    })
    render(<DependenciesPanel issueId="current" teamId="t" workflowStates={states} />)

    fireEvent.click(screen.getByText('Add blocked by'))
    fireEvent.click(screen.getByText('Other issue'))

    await waitFor(() =>
      expect(mutate).toHaveBeenCalledWith({
        blocker_id: 'a',
        blocked_id: 'current',
        team_id: 't',
      }),
    )
  })

  it('picker excludes the current issue and already-linked issues (VAL-DEPS-005)', () => {
    hooks.useIssueDependencies.mockReturnValue({
      data: { items: [makeDep('d1', 'current', 'b', 'CUR-1', 'ENG-9')], total: 1, page: 1, size: 100, pages: 1 },
      isLoading: false,
    })
    hooks.useTeamIssuesForPicker.mockReturnValue({
      data: {
        items: [
          { id: 'current', team_id: 't', identifier: 'CUR-1', title: 'Current', status_id: 's-backlog', priority: 4 } as never,
          { id: 'b', team_id: 't', identifier: 'ENG-9', title: 'Linked', status_id: 's-backlog', priority: 3 } as never,
          { id: 'c', team_id: 't', identifier: 'ENG-10', title: 'Free', status_id: 's-backlog', priority: 2 } as never,
        ],
        total: 3,
      },
    })
    render(<DependenciesPanel issueId="current" teamId="t" workflowStates={states} />)

    fireEvent.click(screen.getByText('Add blocked by'))
    // Only "Free" (c) should be offered; Current and Linked are excluded.
    expect(screen.queryByText('Current')).not.toBeInTheDocument()
    expect(screen.queryByText('Linked')).not.toBeInTheDocument()
    expect(screen.getByText('Free')).toBeInTheDocument()
  })
})
