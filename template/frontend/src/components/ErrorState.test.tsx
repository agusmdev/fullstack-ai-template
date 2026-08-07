import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ErrorState } from './ErrorState'

describe('ErrorState', () => {
  it('renders the error message', () => {
    render(<ErrorState error={new Error('Backend unreachable')} />)
    expect(screen.getByText('Backend unreachable')).toBeInTheDocument()
  })

  it('renders a default title when none provided', () => {
    render(<ErrorState error={new Error('boom')} />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('renders a custom title', () => {
    render(<ErrorState error={new Error('boom')} title="Custom title" />)
    expect(screen.getByText('Custom title')).toBeInTheDocument()
  })

  it('renders a retry button when onRetry is provided', () => {
    render(<ErrorState error={new Error('boom')} onRetry={() => {}} />)
    expect(screen.getByRole('button', { name: /Try again/i })).toBeInTheDocument()
  })

  it('omits the retry button when onRetry is absent', () => {
    render(<ErrorState error={new Error('boom')} />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('uses role="alert" for accessibility', () => {
    render(<ErrorState error={new Error('boom')} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })
})
