import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Route } from './index'

vi.mock('@/hooks/useAuthSubmit', () => ({
  useAuthSubmit: () => ({ submit: vi.fn(), isLoading: false }),
}))

describe('HomePage route', () => {
  const HomePage = Route.options.component as React.FC

  it('renders the hero title and subtitle', () => {
    render(<HomePage />)
    expect(screen.getByText('Full-Stack')).toBeInTheDocument()
    expect(screen.getByText('Template')).toBeInTheDocument()
    expect(screen.getByText(/Stop wiring up boilerplate/)).toBeInTheDocument()
  })

  it('renders registration and sign-in CTAs', () => {
    render(<HomePage />)
    expect(screen.getByRole('link', { name: 'Get Started' })).toHaveAttribute('href', '/register')
    // "Sign In" appears in both the hero and the final CTA — both point to /login.
    const signInLinks = screen.getAllByRole('link', { name: 'Sign In' })
    expect(signInLinks.length).toBeGreaterThanOrEqual(1)
    for (const link of signInLinks) {
      expect(link).toHaveAttribute('href', '/login')
    }
  })

  it('renders all six feature cards', () => {
    render(<HomePage />)
    expect(screen.getByText('TanStack Start SSR')).toBeInTheDocument()
    expect(screen.getByText('FastAPI Backend')).toBeInTheDocument()
    expect(screen.getByText('PostgreSQL + SQLAlchemy')).toBeInTheDocument()
    expect(screen.getByText('Authentication Built-in')).toBeInTheDocument()
    expect(screen.getByText('Docker Compose')).toBeInTheDocument()
    expect(screen.getByText('Type-Safe Everything')).toBeInTheDocument()
  })

  it('renders the tech stack split by category', () => {
    render(<HomePage />)
    expect(screen.getAllByText('Frontend').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Backend').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('React 19')).toBeInTheDocument()
    expect(screen.getByText('Tailwind CSS v4')).toBeInTheDocument()
    expect(screen.getByText('SQLAlchemy 2.0')).toBeInTheDocument()
    expect(screen.getByText('Pydantic v2')).toBeInTheDocument()
  })

  it('renders the final CTA section', () => {
    render(<HomePage />)
    expect(screen.getByText('Ready to Ship?')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Start Building/ })).toHaveAttribute('href', '/register')
  })
})
