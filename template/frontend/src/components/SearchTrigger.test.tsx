import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SearchTrigger } from './SearchTrigger'

const toastMock = vi.hoisted(() => ({ info: vi.fn() }))

vi.mock('sonner', () => ({ toast: toastMock }))

describe('SearchTrigger', () => {
  beforeEach(() => toastMock.info.mockReset())
  afterEach(() => vi.clearAllMocks())

  it('renders a search affordance with an accessible label', () => {
    render(<SearchTrigger />)
    expect(screen.getByLabelText('Search and run commands')).toBeInTheDocument()
  })

  it('shows the ⌘K keyboard hint', () => {
    render(<SearchTrigger />)
    expect(screen.getByText('⌘K')).toBeInTheDocument()
  })

  it('shows a coming-soon toast when clicked', () => {
    render(<SearchTrigger />)
    fireEvent.click(screen.getByLabelText('Search and run commands'))
    expect(toastMock.info).toHaveBeenCalledWith('Command palette coming soon')
  })
})
