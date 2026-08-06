import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CyclePicker } from './CyclePicker'
import type { Cycle } from '@/types/cycle'

const cycles: Cycle[] = [
  {
    id: 'c-1',
    team_id: 't',
    name: 'Sprint 1',
    starts_at: '2000-01-01',
    ends_at: '2000-01-14',
    completed_at: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'c-2',
    team_id: 't',
    name: 'Sprint 2',
    starts_at: '2099-01-01',
    ends_at: '2099-01-14',
    completed_at: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
]

describe('CyclePicker', () => {
  it('shows "No cycle" when value is null', () => {
    render(
      <CyclePicker value={null} onChange={vi.fn()} cycles={cycles} />,
    )
    expect(screen.getByText('No cycle')).toBeInTheDocument()
  })

  it('shows the current cycle name when a value is set', () => {
    render(
      <CyclePicker value="c-1" onChange={vi.fn()} cycles={cycles} />,
    )
    expect(screen.getByText('Sprint 1')).toBeInTheDocument()
  })

  it('calls onChange with cycle id when a cycle is selected (VAL-CYCLES-005)', () => {
    const onChange = vi.fn()
    render(
      <CyclePicker value={null} onChange={onChange} cycles={cycles} />,
    )
    // Open the dropdown.
    fireEvent.click(screen.getByText('No cycle'))
    // Pick Sprint 2.
    fireEvent.click(screen.getByText('Sprint 2'))
    expect(onChange).toHaveBeenCalledWith('c-2')
  })

  it('calls onChange with null when "No cycle" is selected', () => {
    const onChange = vi.fn()
    render(
      <CyclePicker value="c-1" onChange={onChange} cycles={cycles} />,
    )
    // Open the dropdown.
    fireEvent.click(screen.getByText('Sprint 1'))
    // Pick "No cycle".
    fireEvent.click(screen.getByText('No cycle'))
    expect(onChange).toHaveBeenCalledWith(null)
  })

  it('shows phase badges for cycles (VAL-CYCLES-008)', () => {
    render(
      <CyclePicker value={null} onChange={vi.fn()} cycles={cycles} />,
    )
    fireEvent.click(screen.getByText('No cycle'))
    // Sprint 1 (past) and Sprint 2 (upcoming) both show phase badges.
    expect(screen.getByText('past')).toBeInTheDocument()
    expect(screen.getByText('upcoming')).toBeInTheDocument()
  })
})
