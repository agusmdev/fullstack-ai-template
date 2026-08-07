import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { ProjectFormDialog } from './ProjectFormDialog'
import { PROJECT_NAME_MAX } from '@/features/projects/project-schemas'
import type {
  CreateProjectInput,
  UpdateProjectInput,
} from '@/hooks/useProjects'
import type { Project } from '@/types/project'

const createMock = vi.hoisted(() => ({
  mutateAsync: vi.fn(),
  isPending: false,
}))
const updateMock = vi.hoisted(() => ({
  mutateAsync: vi.fn(),
  isPending: false,
}))

vi.mock('@/hooks/useProjects', () => ({
  useCreateProject: () => createMock,
  useUpdateProject: () => updateMock,
}))

const mockProject: Project = {
  id: 'p-1',
  team_id: 't-1',
  name: 'Q3 Launch',
  status: 'planned',
  lead_id: 'u-1',
  target_date: '2026-09-30',
  description: 'desc',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

function typeValue(el: HTMLElement, value: string) {
  fireEvent.change(el, { target: { value } })
  fireEvent.blur(el)
}

function renderDialog(
  overrides: Partial<React.ComponentProps<typeof ProjectFormDialog>> = {},
) {
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

describe('ProjectFormDialog (create mode)', () => {
  beforeEach(() => {
    createMock.mutateAsync.mockReset()
    createMock.mutateAsync.mockResolvedValue({})
    createMock.isPending = false
    updateMock.mutateAsync.mockReset()
    updateMock.isPending = false
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

describe('ProjectFormDialog (edit mode)', () => {
  beforeEach(() => {
    createMock.mutateAsync.mockReset()
    updateMock.mutateAsync.mockReset()
    updateMock.mutateAsync.mockResolvedValue({})
    createMock.isPending = false
    updateMock.isPending = false
  })

  it('shows edit-mode title and pre-fills existing values', () => {
    renderDialog({ project: mockProject })
    expect(screen.getByText('Edit project')).toBeInTheDocument()
    const nameInput = screen.getByPlaceholderText('Project name') as HTMLInputElement
    expect(nameInput.value).toBe('Q3 Launch')
    // Status pre-filled (Planned)
    expect(screen.getByText('Planned')).toBeInTheDocument()
    // Lead pre-filled (Ada Lovelace, not Unassigned)
    expect(screen.getByText('Ada Lovelace')).toBeInTheDocument()
  })

  it('pre-fills the target date', () => {
    renderDialog({ project: mockProject })
    const dateInput = screen.getByLabelText('Target date') as HTMLInputElement
    expect(dateInput.value).toBe('2026-09-30')
  })

  it('patches via useUpdateProject and closes on submit', async () => {
    const { onOpenChange } = renderDialog({ project: mockProject })
    const submitBtn = await screen.findByRole('button', { name: /save changes/i })
    await waitFor(() => expect(submitBtn).toBeEnabled())
    fireEvent.click(submitBtn)

    await waitFor(() => expect(updateMock.mutateAsync).toHaveBeenCalledTimes(1))
    const payload = updateMock.mutateAsync.mock.calls[0][0] as UpdateProjectInput
    expect(payload.id).toBe('p-1')
    expect(payload.team_id).toBe('t-1')
    expect(payload.name).toBe('Q3 Launch')
    expect(payload.status).toBe('planned')
    expect(payload.lead_id).toBe('u-1')
    expect(payload.target_date).toBe('2026-09-30')
    // Create hook must NOT be called in edit mode.
    expect(createMock.mutateAsync).not.toHaveBeenCalled()
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false))
  })

  it('reflects an edited status in the PATCH payload', async () => {
    renderDialog({ project: mockProject })
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /save changes/i })).toBeEnabled(),
    )
    // Change status via the dropdown: open it and pick "In Progress"
    fireEvent.click(screen.getByText('Planned'))
    fireEvent.click(screen.getByText('In Progress'))
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }))

    await waitFor(() => expect(updateMock.mutateAsync).toHaveBeenCalledTimes(1))
    const payload = updateMock.mutateAsync.mock.calls[0][0] as UpdateProjectInput
    expect(payload.status).toBe('started')
  })

  it('keeps the dialog open on backend error', async () => {
    updateMock.mutateAsync.mockRejectedValue(new Error('boom'))
    const { onOpenChange } = renderDialog({ project: mockProject })
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /save changes/i })).toBeEnabled(),
    )
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }))

    await waitFor(() => expect(updateMock.mutateAsync).toHaveBeenCalled())
    expect(onOpenChange).not.toHaveBeenCalled()
  })
})
