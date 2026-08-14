import React from 'react'
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Input } from './input'

describe('Input', () => {
  it('renders an input with the given placeholder', () => {
    render(<Input placeholder="Type here" />)
    expect(screen.getByPlaceholderText('Type here')).toBeInTheDocument()
  })

  it('defaults to a textbox when no type is provided', () => {
    render(<Input placeholder="p" />)
    // React omits the attribute when type is undefined; the browser defaults to text.
    expect(screen.getByRole('textbox')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('p').getAttribute('type')).toBeFalsy()
  })

  it('forwards the type prop', () => {
    render(<Input type="email" placeholder="e" />)
    expect(screen.getByPlaceholderText('e')).toHaveAttribute('type', 'email')
  })

  it('supports controlled value and onChange', () => {
    function Harness() {
      const [v, setV] = React.useState('')
      return <Input value={v} onChange={(e) => setV(e.target.value)} placeholder="c" aria-label="c" />
    }
    render(<Harness />)
    const el = screen.getByPlaceholderText('c')
    fireEvent.change(el, { target: { value: 'hi' } })
    expect(el).toHaveValue('hi')
  })

  it('forwards the disabled attribute', () => {
    render(<Input disabled placeholder="d" />)
    expect(screen.getByPlaceholderText('d')).toBeDisabled()
  })
})
