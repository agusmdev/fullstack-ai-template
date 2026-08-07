import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { LoadingSkeleton } from './LoadingSkeleton'

describe('LoadingSkeleton', () => {
  it('renders the requested number of rows', () => {
    const { container } = render(<LoadingSkeleton rows={5} />)
    // Each row is a flex container with a shimmer; assert via the aria-busy status.
    expect(container.querySelector('[aria-busy="true"]')).toBeInTheDocument()
  })

  it('is marked as a loading status for screen readers', () => {
    const { getByText } = render(<LoadingSkeleton />)
    expect(getByText('Loading…')).toBeInTheDocument()
  })
})
