import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Label } from './label'

describe('Label', () => {
  it('renders a <label> with its children', () => {
    render(<Label>Email</Label>)
    const el = screen.getByText('Email')
    expect(el.tagName).toBe('LABEL')
  })

  it('forwards the htmlFor attribute', () => {
    render(<Label htmlFor="email-field">Email</Label>)
    expect(screen.getByText('Email')).toHaveAttribute('for', 'email-field')
  })

  it('applies the base label classes', () => {
    render(<Label>X</Label>)
    expect(screen.getByText('X').className).toContain('text-sm')
  })
})
