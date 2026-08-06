import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { EmptyState } from './EmptyState'
import { Button } from '@/components/ui/button'

describe('EmptyState', () => {
  it('renders the title and description', () => {
    render(<EmptyState title="No issues yet" description="Create one to get started" />)
    expect(screen.getByText('No issues yet')).toBeInTheDocument()
    expect(screen.getByText('Create one to get started')).toBeInTheDocument()
  })

  it('renders an optional action', () => {
    render(
      <EmptyState
        title="Empty"
        action={<Button>Create issue</Button>}
      />,
    )
    expect(screen.getByRole('button', { name: 'Create issue' })).toBeInTheDocument()
  })

  it('does not render a description when omitted', () => {
    render(<EmptyState title="Just a title" />)
    expect(screen.getByText('Just a title')).toBeInTheDocument()
  })
})
