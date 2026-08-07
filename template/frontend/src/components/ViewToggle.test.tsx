import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ViewToggle } from './ViewToggle'

describe('ViewToggle', () => {
  it('renders both List and Board links', () => {
    render(<ViewToggle teamKey="ENG" active="list" search={{ sort: 'newest' }} />)
    expect(screen.getByLabelText('List view')).toBeInTheDocument()
    expect(screen.getByLabelText('Board view')).toBeInTheDocument()
    expect(screen.getByText('List')).toBeInTheDocument()
    expect(screen.getByText('Board')).toBeInTheDocument()
  })

  it('marks the active view with aria-current', () => {
    const { rerender } = render(
      <ViewToggle teamKey="ENG" active="list" search={{ sort: 'newest' }} />,
    )
    expect(screen.getByLabelText('List view')).toHaveAttribute('aria-current', 'page')
    expect(screen.getByLabelText('Board view')).not.toHaveAttribute('aria-current')

    rerender(<ViewToggle teamKey="ENG" active="board" search={{ sort: 'newest' }} />)
    expect(screen.getByLabelText('Board view')).toHaveAttribute('aria-current', 'page')
    expect(screen.getByLabelText('List view')).not.toHaveAttribute('aria-current')
  })
})
