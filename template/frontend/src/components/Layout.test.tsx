import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Layout } from './Layout'

// Layout renders <Navigation /> and <Outlet />. Mock both to keep this test
// hermetic and focused on Layout's own composition (it mounts nav + a main slot).
vi.mock('./Navigation', () => ({
  Navigation: () => React.createElement('nav', { 'data-testid': 'nav' }),
}))

vi.mock('@tanstack/react-router', () => ({
  Outlet: () => React.createElement('div', { 'data-testid': 'outlet' }, 'page content'),
}))

describe('Layout', () => {
  it('renders the Navigation', () => {
    render(<Layout />)
    expect(screen.getByTestId('nav')).toBeInTheDocument()
  })

  it('renders the routed page via Outlet', () => {
    render(<Layout />)
    expect(screen.getByTestId('outlet')).toBeInTheDocument()
    expect(screen.getByText('page content')).toBeInTheDocument()
  })

  it('renders a <main> landmark for page content', () => {
    const { container } = render(<Layout />)
    expect(container.querySelector('main')).toBeInTheDocument()
  })
})
