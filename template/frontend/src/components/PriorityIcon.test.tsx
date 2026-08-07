import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { PriorityIcon, priorityLabel } from './PriorityIcon'

describe('PriorityIcon', () => {
  it('renders without crashing for all priority ranks', () => {
    for (let p = 0; p <= 4; p++) {
      const { container } = render(<PriorityIcon priority={p} />)
      expect(container.querySelector('svg')).toBeTruthy()
    }
  })
})

describe('priorityLabel', () => {
  it('maps ranks to canonical labels', () => {
    expect(priorityLabel(0)).toBe('Urgent')
    expect(priorityLabel(1)).toBe('High')
    expect(priorityLabel(4)).toBe('No priority')
  })

  it('falls back to "No priority" for unknown ranks', () => {
    expect(priorityLabel(99)).toBe('No priority')
  })
})
