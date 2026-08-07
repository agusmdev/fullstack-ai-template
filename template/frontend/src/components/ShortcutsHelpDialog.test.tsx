import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import { ShortcutsHelpDialog } from './ShortcutsHelpDialog'
import {
  KeyboardShortcutsProvider,
  useKeyboardShortcuts,
} from '@/contexts/KeyboardShortcutsContext'
import { CommandPaletteProvider } from '@/contexts/CommandPaletteContext'

vi.mock('@/hooks/useTeamRole', () => ({
  useTeamRole: () => ({ canWrite: true, role: 'admin', isLoading: false, canAdmin: true }),
}))

vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-router')>(
    '@tanstack/react-router',
  )
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  }
})

function Harness() {
  const { openShortcutsHelp } = useKeyboardShortcuts()
  return (
    <div>
      <button onClick={openShortcutsHelp}>help</button>
      <ShortcutsHelpDialog />
    </div>
  )
}

function renderIt() {
  return render(
    <CommandPaletteProvider>
      <KeyboardShortcutsProvider teamKey="ENG">
        <Harness />
      </KeyboardShortcutsProvider>
    </CommandPaletteProvider>,
  )
}

describe('ShortcutsHelpDialog', () => {
  afterEach(() => cleanup())

  it('opens with the full shortcut reference (VAL-SHORTCUTS-007)', () => {
    renderIt()
    fireEvent.click(screen.getByText('help'))
    expect(screen.getByText('Keyboard shortcuts')).toBeInTheDocument()
    // A representative shortcut from each documented area is present.
    expect(screen.getByText('Open command palette')).toBeInTheDocument()
    expect(screen.getByText('Create issue')).toBeInTheDocument()
    expect(screen.getByText('Go to Issues')).toBeInTheDocument()
    expect(screen.getByText('Previous issue (in drawer)')).toBeInTheDocument()
  })

  it('renders the key hints as badges', () => {
    renderIt()
    fireEvent.click(screen.getByText('help'))
    expect(screen.getByText('⌘K')).toBeInTheDocument()
    expect(screen.getByText('C')).toBeInTheDocument()
    expect(screen.getByText('G I')).toBeInTheDocument()
  })
})
