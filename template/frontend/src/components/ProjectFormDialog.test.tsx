import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { ProjectFormDialog } from './ProjectFormDialog'
import { PROJECT_NAME_MAX } from '@/features/projects/project-schemas'
import type { CreateProjectInput } from '@/hooks/useProjects'

const createMock = vi.hoisted(() => ({
  mutateAsync: vi.fn(),
  isPending: false,
}))

vi.mock('@/hooks/useProjects', () => ({
  useCreateProject: () => createMock,
}))

function typeValue(el: HTMLElement, value: string) {
  fireEvent.change(el, { target: { value } })
  fireEvent.blur(el)
}

function renderDialog(overrides: Partial<React.ComponentProps<typeof ProjectFormDialog>> = {}) {
  const onOpenChange = vi.fn()
  const utils = render(
    <ProjectFormDialog
      open
      onOpenChange={onOpenChange}
      teamId="t-1"
      members={[{ id: 'u-1', name: 'Ada Lovelace' }]}
      {...overrides}
    />,
  )
  return { ...utils, onOpenChange }
}

describe('ProjectFormDialog', () => {
  beforeEach(() => {
    createMock.mutateAsync.mockReset()
    createMock.mutateAsync.mockResolvedValue({})
    createMock.isPending = false
  })

  it('opens with a blank name and documented defaults (VAL-PROJECTS-002)', () => {
    renderDialog()
    const nameInput = screen.getByPlaceholderText('Project name') as HTMLInputElement
    expect(nameInput.value).toBe('')
    // Default status = Planned (non-terminal)
    expect(screen.getByText('Planned')).toBeInTheDocument()
    // Default lead = Unassigned
    expect(screen.getByText('Unassigned')).toBeInTheDocument()
  })

  it('disables submit while name is empty (VAL-PROJECTS-001)', () => {
    renderDialog()
    expect(screen.getByRole('button', { name: /create project/i })).toBeDisabled()
  })

  it('rejects whitespace-only name (VAL-PROJECTS-001)', async () => {
    renderDialog()
    typeValue(screen.getByPlaceholderText('Project name'), '   ')
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /create project/i })).toBeDisabled()
    })
  })

  it('enables submit for a valid name', async () => {
    renderDialog()
    typeValue(screen.getByPlaceholderText('Project name'), 'Q3 Launch')
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /create project/i })).toBeEnabled()
    })
  })

  it('enforces the name maxLength on the input', () => {
    renderDialog()
    const nameInput = screen.getByPlaceholderText('Project name') as HTMLInputElement
    expect(nameInput.maxLength).toBe(PROJECT_NAME_MAX)
  })

  it('creates with name and defaults and closes', async () => {
    const { onOpenChange } = renderDialog()
    typeValue(screen.getByPlaceholderText('Project name'), 'My project')
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /create project/i })).toBeEnabled(),
    )
    fireEvent.click(screen.getByRole('button', { name: /create project/i }))

    await waitFor(() => expect(createMock.mutateAsync).toHaveBeenCalledTimes(1))
    const payload = createMock.mutateAsync.mock.calls[0][0] as CreateProjectInput
    expect(payload.name).toBe('My project')
    expect(payload.status).toBe('planned')
    expect(payload.lead_id).toBeNull()
    expect(payload.target_date).toBeNull()
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false))
  })

  it('keeps the dialog open on backend error', async () => {
    createMock.mutateAsync.mockRejectedValue(new Error('boom'))
    const { onOpenChange } = renderDialog()
    typeValue(screen.getByPlaceholderText('Project name'), 'Keep me')
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /create project/i })).toBeEnabled(),
    )
    fireEvent.click(screen.getByRole('button', { name: /create project/i }))

    await waitFor(() => expect(createMock.mutateAsync).toHaveBeenCalled())
    expect((screen.getByPlaceholderText('Project name') as HTMLInputElement).value).toBe('Keep me')
    expect(onOpenChange).not.toHaveBeenCalled()
  })

  it('does not fire the API on submit with an empty name', () => {
    renderDialog()
    const form = screen.getByPlaceholderText('Project name').closest('form')!
    fireEvent.submit(form)
    expect(createMock.mutateAsync).not.toHaveBeenCalled()
  })
})
