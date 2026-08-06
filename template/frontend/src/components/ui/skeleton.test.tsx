import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { Skeleton } from './skeleton'

describe('Skeleton', () => {
  it('renders a shimmer block', () => {
    const { container } = render(<Skeleton className="h-4 w-10" />)
    const el = container.querySelector('[data-slot="skeleton"]')
    expect(el).toBeInTheDocument()
    expect(el?.className).toContain('animate-pulse')
  })
})
