import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ProjectPicker } from './ProjectPicker'
import type { Project } from '@/types/project'

const projects: Project[] = [
  { id: 'p-1', team_id: 't', name: 'Q3 Launch', status: 'planned', lead_id: null, target_date: null, description: null, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
  { id: 'p-2', team_id: 't', name: 'Migration', status: 'started', lead_id: null, target_date: null, description: null, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
]

describe('ProjectPicker', () => {
  it('shows "No project" when no value is set', () => {
    render(<ProjectPicker value={null} onChange={vi.fn()} projects={projects} />)
    expect(screen.getByText('No project')).toBeInTheDocument()
  })

  it('shows the current project name when a value is set', () => {
    render(<ProjectPicker value="p-1" onChange={vi.fn()} projects={projects} />)
    expect(screen.getByText('Q3 Launch')).toBeInTheDocument()
  })

  it('lists all projects + "No project" when opened', () => {
    render(<ProjectPicker value={null} onChange={vi.fn()} projects={projects} />)
    // Trigger is the button showing "No project".
    fireEvent.click(screen.getByText('No project'))
    // The dropdown content now lists every project.
    expect(screen.getByText('Q3 Launch')).toBeInTheDocument()
    expect(screen.getByText('Migration')).toBeInTheDocument()
    // "No project" now appears twice (trigger + menu item).
    expect(screen.getAllByText('No project').length).toBe(2)
  })

  it('reports the selected project id via onChange', () => {
    const onChange = vi.fn()
    render(<ProjectPicker value={null} onChange={onChange} projects={projects} />)
    fireEvent.click(screen.getByText('No project'))
    fireEvent.click(screen.getByText('Migration'))
    expect(onChange).toHaveBeenCalledWith('p-2')
  })

  it('reports null when clearing the project (VAL-PROJECTS-008)', () => {
    const onChange = vi.fn()
    render(<ProjectPicker value="p-1" onChange={onChange} projects={projects} />)
    // Open and select "No project".
    fireEvent.click(screen.getByText('Q3 Launch'))
    // The "No project" item with the Ban icon — find by role menuitem.
    const noProjectItem = screen.getAllByRole('menuitem')[0]
    fireEvent.click(noProjectItem)
    expect(onChange).toHaveBeenCalledWith(null)
  })
})
