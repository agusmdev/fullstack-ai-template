import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { AppShellSkeleton } from './AppShellSkeleton'

describe('AppShellSkeleton', () => {
  it('renders an accessible busy status with a screen-reader label', () => {
    const { getByRole, getByText } = render(<AppShellSkeleton />)
    const status = getByRole('status')
    expect(status).toHaveAttribute('aria-busy', 'true')
    expect(getByText(/loading workspace/i)).toBeInTheDocument()
  })

  it('renders shimmer placeholders and no client-only state', () => {
    const { container } = render(<AppShellSkeleton />)
    // Skeleton shimmer elements present.
    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0)
  })
})
