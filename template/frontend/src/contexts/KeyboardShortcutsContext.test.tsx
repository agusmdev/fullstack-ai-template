import { describe, it, expect, vi, afterEach } from 'vitest'
import { useEffect, useState } from 'react'
import { render, screen, act, cleanup } from '@testing-library/react'
import {
  KeyboardShortcutsProvider,
  useKeyboardShortcuts,
} from './KeyboardShortcutsContext'
import { CommandPaletteProvider, useCommandPalette } from './CommandPaletteContext'

// --- Module mocks --------------------------------------------------------
// The provider depends on the router's navigate + team role. Mock both so the
// tests exercise the keydown logic without a router/team data setup.
const navigateSpy = vi.fn()

vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-router')>(
    '@tanstack/react-router',
  )
  return {
    ...actual,
    useNavigate: () => navigateSpy,
  }
})

vi.mock('@/hooks/useTeamRole', () => ({
  useTeamRole: () => ({ canWrite: true, role: 'admin', isLoading: false, canAdmin: true }),
}))

/** Dispatch a keydown from a given element (defaults to window). */
function pressKey(
  key: string,
  target?: Element,
  modifiers?: { metaKey?: boolean; ctrlKey?: boolean; altKey?: boolean },
) {
  const event = new KeyboardEvent('keydown', {
    key,
    bubbles: true,
    cancelable: true,
    metaKey: modifiers?.metaKey ?? false,
    ctrlKey: modifiers?.ctrlKey ?? false,
    altKey: modifiers?.altKey ?? false,
  })
  if (target) Object.defineProperty(event, 'target', { value: target })
  act(() => {
    ;(target ?? window).dispatchEvent(event)
  })
  return event
}

/** Test consumer exposing context state + an issue-nav registration. */
function Probe() {
  const { registerIssueNav, shortcutsHelpOpen } = useKeyboardShortcuts()
  const { createIssueOpen } = useCommandPalette()
  const [selected, setSelected] = useState('2')
  useEffect(() => {
    return registerIssueNav({ ids: ['1', '2', '3'], currentId: selected, select: setSelected })
  }, [registerIssueNav, selected])
  return (
    <div>
      <span data-testid="create">{Number(createIssueOpen)}</span>
      <span data-testid="selected">{selected}</span>
      <span data-testid="help">{Number(shortcutsHelpOpen)}</span>
      <input data-testid="text-input" />
      <textarea data-testid="text-area" />
    </div>
  )
}

function renderProvider() {
  navigateSpy.mockClear()
  return render(
    <CommandPaletteProvider>
      <KeyboardShortcutsProvider teamKey="ENG">
        <Probe />
      </KeyboardShortcutsProvider>
    </CommandPaletteProvider>,
  )
}

describe('KeyboardShortcutsProvider', () => {
  afterEach(() => {
    cleanup()
    vi.clearAllMocks()
  })

  it('`c` opens the Create Issue dialog (VAL-SHORTCUTS-001)', () => {
    renderProvider()
    expect(screen.getByTestId('create').textContent).toBe('0')
    pressKey('c')
    expect(screen.getByTestId('create').textContent).toBe('1')
  })

  it('uppercase `C` also triggers create (caps/shift tolerant)', () => {
    renderProvider()
    pressKey('C')
    expect(screen.getByTestId('create').textContent).toBe('1')
  })

  it('`c` is suppressed while typing in an input (VAL-SHORTCUTS-005)', () => {
    renderProvider()
    pressKey('c', screen.getByTestId('text-input'))
    expect(screen.getByTestId('create').textContent).toBe('0')
  })

  it('`c` is suppressed while typing in a textarea (VAL-SHORTCUTS-005)', () => {
    renderProvider()
    pressKey('c', screen.getByTestId('text-area'))
    expect(screen.getByTestId('create').textContent).toBe('0')
  })

  // --- Modifier-key guard (Cmd/Ctrl/Alt must not trigger single-key shortcuts) ---
  it('Cmd+C does NOT open Create Issue and does not preventDefault', () => {
    renderProvider()
    const event = pressKey('c', undefined, { metaKey: true })
    expect(screen.getByTestId('create').textContent).toBe('0')
    expect(event.defaultPrevented).toBe(false)
  })

  it('Ctrl+C does NOT open Create Issue and does not preventDefault', () => {
    renderProvider()
    const event = pressKey('c', undefined, { ctrlKey: true })
    expect(screen.getByTestId('create').textContent).toBe('0')
    expect(event.defaultPrevented).toBe(false)
  })

  it('Alt+C does NOT open Create Issue and does not preventDefault', () => {
    renderProvider()
    const event = pressKey('c', undefined, { altKey: true })
    expect(screen.getByTestId('create').textContent).toBe('0')
    expect(event.defaultPrevented).toBe(false)
  })

  it('Cmd+G does not arm the g-sequence', () => {
    renderProvider()
    pressKey('g', undefined, { metaKey: true })
    pressKey('i') // not part of an armed sequence
    expect(navigateSpy).not.toHaveBeenCalled()
  })

  it('Ctrl+G does not arm the g-sequence', () => {
    renderProvider()
    pressKey('g', undefined, { ctrlKey: true })
    pressKey('i')
    expect(navigateSpy).not.toHaveBeenCalled()
  })

  it('Cmd+[ does not navigate issues', () => {
    renderProvider()
    // selected starts at '2'; Cmd+[ must not move to '1'
    pressKey('[', undefined, { metaKey: true })
    expect(screen.getByTestId('selected').textContent).toBe('2')
  })

  it('Cmd+] does not navigate issues', () => {
    renderProvider()
    pressKey(']', undefined, { metaKey: true })
    expect(screen.getByTestId('selected').textContent).toBe('2')
  })

  it('`g` then `i` navigates to Issues (VAL-SHORTCUTS-002)', () => {
    renderProvider()
    pressKey('g')
    pressKey('i')
    expect(navigateSpy).toHaveBeenCalledTimes(1)
    expect(navigateSpy).toHaveBeenCalledWith({ to: '/$team/issues', params: { team: 'ENG' } })
  })

  it('a non-matching key after `g` cancels the sequence', () => {
    renderProvider()
    pressKey('g')
    pressKey('x')
    pressKey('i') // no longer part of the sequence
    expect(navigateSpy).not.toHaveBeenCalled()
  })

  it('`g` then `i` is suppressed while typing in an input', () => {
    renderProvider()
    pressKey('g', screen.getByTestId('text-input'))
    pressKey('i')
    expect(navigateSpy).not.toHaveBeenCalled()
  })

  it('`[` and `]` navigate prev/next issue (VAL-SHORTCUTS-003)', () => {
    renderProvider()
    expect(screen.getByTestId('selected').textContent).toBe('2')
    pressKey(']')
    expect(screen.getByTestId('selected').textContent).toBe('3')
    pressKey(']')
    // already at the end → no change
    expect(screen.getByTestId('selected').textContent).toBe('3')
    pressKey('[')
    expect(screen.getByTestId('selected').textContent).toBe('2')
    pressKey('[')
    expect(screen.getByTestId('selected').textContent).toBe('1')
    pressKey('[')
    // already at the start → no change
    expect(screen.getByTestId('selected').textContent).toBe('1')
  })

  it('`[`/`]` are suppressed while typing in an input (VAL-SHORTCUTS-005)', () => {
    renderProvider()
    pressKey(']', screen.getByTestId('text-input'))
    expect(screen.getByTestId('selected').textContent).toBe('2')
  })

  it('`?` opens the shortcuts help reference (VAL-SHORTCUTS-007)', () => {
    renderProvider()
    expect(screen.getByTestId('help').textContent).toBe('0')
    pressKey('?')
    expect(screen.getByTestId('help').textContent).toBe('1')
  })

  it('useKeyboardShortcuts throws outside the provider', () => {
    const errSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<Probe />)).toThrow(/must be used within a KeyboardShortcutsProvider/)
    errSpy.mockRestore()
    cleanup()
  })
})
