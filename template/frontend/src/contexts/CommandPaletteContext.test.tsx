import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, act, cleanup } from '@testing-library/react'
import { CommandPaletteProvider, useCommandPalette } from './CommandPaletteContext'

/** Test consumer: exposes context actions via buttons so tests can assert state. */
function Probe() {
  const {
    paletteOpen,
    createIssueOpen,
    createProjectOpen,
    createCycleOpen,
    openPalette,
    closePalette,
    togglePalette,
    openCreateIssue,
    openCreateProject,
    openCreateCycle,
  } = useCommandPalette()
  return (
    <div>
      <span data-testid="state">
        {Number(paletteOpen)}-{Number(createIssueOpen)}-{Number(createProjectOpen)}-
        {Number(createCycleOpen)}
      </span>
      <button onClick={openPalette}>open</button>
      <button onClick={closePalette}>close</button>
      <button onClick={togglePalette}>toggle</button>
      <button onClick={openCreateIssue}>createIssue</button>
      <button onClick={openCreateProject}>createProject</button>
      <button onClick={openCreateCycle}>createCycle</button>
    </div>
  )
}

function renderProvider() {
  return render(
    <CommandPaletteProvider>
      <Probe />
    </CommandPaletteProvider>,
  )
}

function state() {
  return screen.getByTestId('state').textContent
}

/** Dispatch a real window keydown (the global Cmd+K listener target). */
function pressCmdK() {
  act(() => {
    window.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'k', metaKey: true, bubbles: true }),
    )
  })
}

describe('CommandPaletteProvider', () => {
  afterEach(() => {
    cleanup()
    vi.clearAllMocks()
  })

  it('starts with everything closed', () => {
    renderProvider()
    expect(state()).toBe('0-0-0-0')
  })

  it('openPalette/closePalette/togglePalette control the palette state', () => {
    renderProvider()
    fireEvent.click(screen.getByText('open'))
    expect(state()).toBe('1-0-0-0')
    fireEvent.click(screen.getByText('close'))
    expect(state()).toBe('0-0-0-0')
    fireEvent.click(screen.getByText('toggle'))
    expect(state()).toBe('1-0-0-0')
    fireEvent.click(screen.getByText('toggle'))
    expect(state()).toBe('0-0-0-0')
  })

  it('opening a create action closes the palette and opens that dialog', () => {
    renderProvider()
    fireEvent.click(screen.getByText('open'))
    expect(state()).toBe('1-0-0-0')
    fireEvent.click(screen.getByText('createIssue'))
    expect(state()).toBe('0-1-0-0')
    fireEvent.click(screen.getByText('open'))
    fireEvent.click(screen.getByText('createProject'))
    expect(state()).toBe('0-0-1-0')
    fireEvent.click(screen.getByText('open'))
    fireEvent.click(screen.getByText('createCycle'))
    expect(state()).toBe('0-0-0-1')
  })

  it('Cmd+K toggles the palette (VAL-CMDK-001)', () => {
    renderProvider()
    expect(state()).toBe('0-0-0-0')
    pressCmdK()
    expect(state()).toBe('1-0-0-0')
    pressCmdK()
    expect(state()).toBe('0-0-0-0')
  })

  it('Ctrl+K toggles the palette on non-mac (VAL-CMDK-001)', () => {
    renderProvider()
    act(() => {
      window.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true }),
      )
    })
    expect(state()).toBe('1-0-0-0')
  })

  it('Cmd+K prevents the default browser search behavior', () => {
    renderProvider()
    const event = new KeyboardEvent('keydown', {
      key: 'k',
      metaKey: true,
      bubbles: true,
      cancelable: true,
    })
    const spy = vi.spyOn(event, 'preventDefault')
    act(() => window.dispatchEvent(event))
    expect(spy).toHaveBeenCalled()
  })

  it('useCommandPalette throws when used outside the provider', () => {
    // Suppress the expected error log from React.
    const errSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<Probe />)).toThrow(
      /must be used within a CommandPaletteProvider/,
    )
    errSpy.mockRestore()
    cleanup()
  })
})
