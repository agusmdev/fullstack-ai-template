import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import { toast } from 'sonner'
import { SearchTrigger } from './SearchTrigger'
import {
  CommandPaletteProvider,
  useCommandPalette,
} from '@/contexts/CommandPaletteContext'

/** Shows the palette open state so the trigger can be asserted to open it. */
function StateProbe() {
  const { paletteOpen } = useCommandPalette()
  return <span data-testid="palette-open">{String(paletteOpen)}</span>
}

function renderTrigger() {
  return render(
    <CommandPaletteProvider>
      <SearchTrigger />
      <StateProbe />
    </CommandPaletteProvider>,
  )
}

describe('SearchTrigger', () => {
  beforeEach(() => vi.clearAllMocks())
  afterEach(() => cleanup())

  it('renders a search affordance with an accessible label', () => {
    renderTrigger()
    expect(screen.getByLabelText('Search and run commands')).toBeInTheDocument()
  })

  it('shows the ⌘K keyboard hint', () => {
    renderTrigger()
    expect(screen.getByText('⌘K')).toBeInTheDocument()
  })

  it('opens the command palette when clicked (VAL-CMDK-002)', () => {
    const toastSpy = vi.spyOn(toast, 'info')
    renderTrigger()
    // Palette closed initially.
    expect(screen.getByTestId('palette-open').textContent).toBe('false')
    fireEvent.click(screen.getByLabelText('Search and run commands'))
    // Palette is now open.
    expect(screen.getByTestId('palette-open').textContent).toBe('true')
    // No "coming soon" toast is fired anymore.
    expect(toastSpy).not.toHaveBeenCalled()
    toastSpy.mockRestore()
  })
})
