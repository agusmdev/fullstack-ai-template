import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from './dropdown'

function MenuHarness({ onSelect }: { onSelect?: (item: string) => void }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger>
        <button>Open</button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuLabel>Label</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => onSelect?.('a')}>Item A</DropdownMenuItem>
        <DropdownMenuItem onClick={() => onSelect?.('b')}>Item B</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

describe('DropdownMenu', () => {
  it('does not render content until the trigger is clicked', () => {
    render(<MenuHarness />)
    expect(screen.queryByText('Item A')).not.toBeInTheDocument()
  })

  it('opens content on trigger click', () => {
    render(<MenuHarness />)
    fireEvent.click(screen.getByText('Open'))
    expect(screen.getByText('Item A')).toBeInTheDocument()
    expect(screen.getByText('Item B')).toBeInTheDocument()
  })

  it('calls the item handler and closes on selection', () => {
    const onSelect = vi.fn()
    render(<MenuHarness onSelect={onSelect} />)
    fireEvent.click(screen.getByText('Open'))
    fireEvent.click(screen.getByText('Item A'))
    expect(onSelect).toHaveBeenCalledWith('a')
    expect(screen.queryByText('Item A')).not.toBeInTheDocument()
  })

  it('closes on Escape', async () => {
    render(<MenuHarness />)
    fireEvent.click(screen.getByText('Open'))
    expect(screen.getByText('Item A')).toBeInTheDocument()
    fireEvent.keyDown(document, { key: 'Escape' })
    await waitFor(() => {
      expect(screen.queryByText('Item A')).not.toBeInTheDocument()
    })
  })

  it('closes on outside click', async () => {
    render(
      <div>
        <MenuHarness />
        <button>Outside</button>
      </div>,
    )
    fireEvent.click(screen.getByText('Open'))
    expect(screen.getByText('Item A')).toBeInTheDocument()
    // Click outside the dropdown
    fireEvent.mouseDown(screen.getByText('Outside'))
    await waitFor(() => {
      expect(screen.queryByText('Item A')).not.toBeInTheDocument()
    })
  })

  it('sets aria-expanded on the trigger', () => {
    render(<MenuHarness />)
    const trigger = screen.getByText('Open')
    expect(trigger).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(trigger)
    expect(trigger).toHaveAttribute('aria-expanded', 'true')
  })
})
