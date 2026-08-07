import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, cleanup, act } from '@testing-library/react'
import { CommandPalette } from './CommandPalette'
import { CommandPaletteProvider, useCommandPalette } from '@/contexts/CommandPaletteContext'

// --- Mocks ---------------------------------------------------------------

const navigateMock = vi.fn()

vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => navigateMock,
}))

vi.mock('@/hooks/useTeams', () => ({
  useTeams: () => ({
    data: { items: [{ id: 't-1', key: 'ENG', name: 'Engineering' }] },
  }),
}))
vi.mock('@/hooks/useUser', () => ({
  useUser: () => ({
    data: { id: 'u-1', display_name: 'Ada Lovelace', email: 'a@b.c' },
  }),
}))
vi.mock('@/hooks/useTeamRole', () => ({
  useTeamRole: () => ({ canWrite: true, canAdmin: true, role: 'admin' }),
}))
vi.mock('@/hooks/useWorkflowStates', () => ({
  useWorkflowStates: () => ({ data: { items: [{ id: 's-1', name: 'Backlog' }] } }),
}))
vi.mock('@/hooks/useLabels', () => ({
  useLabels: () => ({ data: { items: [{ id: 'l-1', name: 'Bug' }] } }),
}))

// Mock the create dialogs so we can assert their open state from the palette.
vi.mock('@/components/CreateIssueDialog', () => ({
  CreateIssueDialog: ({ open }: { open: boolean }) =>
    open ? <div data-testid="create-issue-dialog">Create Issue Dialog</div> : null,
}))
vi.mock('@/components/ProjectFormDialog', () => ({
  ProjectFormDialog: ({ open }: { open: boolean }) =>
    open ? <div data-testid="create-project-dialog">Create Project Dialog</div> : null,
}))
vi.mock('@/components/CycleFormDialog', () => ({
  CycleFormDialog: ({ open }: { open: boolean }) =>
    open ? <div data-testid="create-cycle-dialog">Create Cycle Dialog</div> : null,
}))

/** Wrapper that opens the palette so tests can interact with it. */
function PaletteHarness({ teamKey = 'ENG' }: { teamKey?: string }) {
  return (
    <CommandPaletteProvider>
      <OpenButton />
      <CommandPalette teamKey={teamKey} />
    </CommandPaletteProvider>
  )
}

function OpenButton() {
  const { openPalette } = useCommandPalette()
  return <button onClick={openPalette}>open-palette</button>
}

function renderPalette(teamKey = 'ENG') {
  return render(<PaletteHarness teamKey={teamKey} />)
}

/** Type into the palette's search input. */
function search(query: string) {
  const input = screen.getByPlaceholderText('Type a command or search…')
  fireEvent.change(input, { target: { value: query } })
}

function pressEscape() {
  // Radix Dialog listens for Escape on the document.
  act(() => {
    document.body.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }),
    )
  })
}

const DEFAULT_ITEMS = ['Issues', 'Board', 'Projects', 'Cycles', 'Views', 'Create issue', 'Create project', 'Create cycle']

describe('CommandPalette', () => {
  beforeEach(() => navigateMock.mockReset())
  afterEach(() => {
    cleanup()
  })

  it('is closed initially and opens via the trigger state', () => {
    renderPalette()
    // Not open yet: no dialog.
    expect(screen.queryByPlaceholderText('Type a command or search…')).not.toBeInTheDocument()
    fireEvent.click(screen.getByText('open-palette'))
    expect(screen.getByPlaceholderText('Type a command or search…')).toBeInTheDocument()
  })

  it('shows the default command set on an empty query (VAL-CMDK-007)', () => {
    renderPalette()
    fireEvent.click(screen.getByText('open-palette'))
    for (const label of DEFAULT_ITEMS) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
  })

  it('fuzzy search narrows results as you type (VAL-CMDK-003)', () => {
    renderPalette()
    fireEvent.click(screen.getByText('open-palette'))
    // Before: Board visible.
    expect(screen.getByText('Board')).toBeInTheDocument()
    search('kanban')
    // After: Board remains, Issues is filtered out.
    expect(screen.getByText('Board')).toBeInTheDocument()
    expect(screen.queryByText('Issues')).not.toBeInTheDocument()
  })

  it('shows a no-results state when nothing matches (VAL-CMDK-008)', () => {
    renderPalette()
    fireEvent.click(screen.getByText('open-palette'))
    search('zzzznomatch')
    expect(screen.getByText(/no results found/i)).toBeInTheDocument()
    expect(screen.queryByText('Issues')).not.toBeInTheDocument()
  })

  it('selecting a navigation target closes the palette and navigates (VAL-CMDK-004)', () => {
    renderPalette('ENG')
    fireEvent.click(screen.getByText('open-palette'))
    fireEvent.click(screen.getByText('Board'))
    expect(navigateMock).toHaveBeenCalledWith({
      to: '/$team/board',
      params: { team: 'ENG' },
    })
    // Palette closed after navigation.
    expect(screen.queryByPlaceholderText('Type a command or search…')).not.toBeInTheDocument()
  })

  it('selecting Create issue opens the create-issue dialog (VAL-CMDK-005)', () => {
    renderPalette('ENG')
    fireEvent.click(screen.getByText('open-palette'))
    fireEvent.click(screen.getByText('Create issue'))
    // Palette closed, create-issue dialog opened.
    expect(screen.queryByPlaceholderText('Type a command or search…')).not.toBeInTheDocument()
    expect(screen.getByTestId('create-issue-dialog')).toBeInTheDocument()
  })

  it('selecting Create project opens the create-project dialog (VAL-CMDK-005)', () => {
    renderPalette('ENG')
    fireEvent.click(screen.getByText('open-palette'))
    fireEvent.click(screen.getByText('Create project'))
    expect(screen.getByTestId('create-project-dialog')).toBeInTheDocument()
    expect(screen.queryByPlaceholderText('Type a command or search…')).not.toBeInTheDocument()
  })

  it('selecting Create cycle opens the create-cycle dialog (VAL-CMDK-005)', () => {
    renderPalette('ENG')
    fireEvent.click(screen.getByText('open-palette'))
    fireEvent.click(screen.getByText('Create cycle'))
    expect(screen.getByTestId('create-cycle-dialog')).toBeInTheDocument()
  })

  it('Esc closes the palette without triggering an action (VAL-CMDK-006)', () => {
    renderPalette('ENG')
    fireEvent.click(screen.getByText('open-palette'))
    expect(screen.getByPlaceholderText('Type a command or search…')).toBeInTheDocument()
    pressEscape()
    // Palette closed.
    expect(screen.queryByPlaceholderText('Type a command or search…')).not.toBeInTheDocument()
    // No navigation or create dialog triggered as a side effect.
    expect(navigateMock).not.toHaveBeenCalled()
    expect(screen.queryByTestId('create-issue-dialog')).not.toBeInTheDocument()
  })
})
