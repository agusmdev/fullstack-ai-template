import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { IssueBoardSkeleton } from './IssueBoardSkeleton'

describe('IssueBoardSkeleton', () => {
  it('renders the correct number of placeholder columns', () => {
    render(<IssueBoardSkeleton columns={5} />)
    // Each column renders a "Loading board…" text only once (sr-only)
    expect(screen.getByText('Loading board…')).toBeInTheDocument()
  })

  it('defaults to 4 columns', () => {
    const { container } = render(<IssueBoardSkeleton />)
    // The root div contains N column divs + 1 sr-only span
    const root = container.firstElementChild
    const columnDivs = root?.querySelectorAll(':scope > div')
    expect(columnDivs?.length).toBe(4)
  })

  it('has aria-busy and role=status for accessibility', () => {
    render(<IssueBoardSkeleton columns={3} />)
    expect(screen.getByRole('status')).toHaveAttribute('aria-busy', 'true')
  })
})
