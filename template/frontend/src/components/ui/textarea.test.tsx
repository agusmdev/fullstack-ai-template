import React from 'react'
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Textarea } from './textarea'

describe('Textarea', () => {
  it('renders a textarea with the given placeholder', () => {
    render(<Textarea placeholder="Write something" />)
    expect(screen.getByPlaceholderText('Write something')).toHaveProperty('tagName', 'TEXTAREA')
  })

  it('supports controlled value and onChange', () => {
    function Harness() {
      const [v, setV] = React.useState('')
      return <Textarea value={v} onChange={(e) => setV(e.target.value)} placeholder="t" />
    }
    render(<Harness />)
    const el = screen.getByPlaceholderText('t') as HTMLTextAreaElement
    fireEvent.change(el, { target: { value: 'long text' } })
    expect(el).toHaveValue('long text')
  })

  it('forwards native attributes (rows, disabled)', () => {
    render(<Textarea rows={4} disabled placeholder="d" />)
    const el = screen.getByPlaceholderText('d') as HTMLTextAreaElement
    expect(el).toHaveAttribute('rows', '4')
    expect(el).toBeDisabled()
  })
})
