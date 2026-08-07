import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
import { SaveViewDialog } from './SaveViewDialog'
import type { CreateViewInput } from '@/hooks/useViews'
import type { IssueUrlSearch } from '@/lib/issue-search'

const createMock = vi.hoisted(() => ({
  mutateAsync: vi.fn(),
  isPending: false,
}))

vi.mock('@/hooks/useViews', () => ({
  useCreateView: () => createMock,
}))

const activeSearch: IssueUrlSearch = {
  status_id: 'st-1',
  priority: 0,
  sort: 'priority',
}

function typeValue(el: HTMLElement, value: string) {
  fireEvent.change(el, { target: { value } })
  fireEvent.blur(el)
}

function renderDialog(
  overrides: Partial<React.ComponentProps<typeof SaveViewDialog>> = {},
) {
  const onOpenChange = vi.fn()
  const utils = render(
    <SaveViewDialog
      open
      onOpenChange={onOpenChange}
      teamId="t-1"
      search={activeSearch}
      {...overrides}
    />,
  )
  return { ...utils, onOpenChange }
}

describe('SaveViewDialog', () => {
  beforeEach(() => {
    createMock.mutateAsync.mockReset()
    createMock.mutateAsync.mockResolvedValue({})
    createMock.isPending = false
  })

  it('opens with a blank name', () => {
    renderDialog()
    const nameInput = screen.getByPlaceholderText('View name') as HTMLInputElement
    expect(nameInput.value).toBe('')
  })

  it('disables submit while name is empty (VAL-VIEWS-002)', () => {
    renderDialog()
    expect(screen.getByRole('button', { name: /save view/i })).toBeDisabled()
  })

  it('rejects whitespace-only name (VAL-VIEWS-002)', async () => {
    renderDialog()
    typeValue(screen.getByPlaceholderText('View name'), '   ')
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /save view/i })).toBeDisabled()
    })
  })

  it('enables submit for a valid name', async () => {
    renderDialog()
    typeValue(screen.getByPlaceholderText('View name'), 'Urgent bugs')
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /save view/i })).toBeEnabled()
    })
  })

  it('saves filters + group_by + order_by captured from the current search (VAL-VIEWS-001)', async () => {
    const { onOpenChange } = renderDialog()
    typeValue(screen.getByPlaceholderText('View name'), 'Urgent bugs')
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /save view/i })).toBeEnabled(),
    )
    fireEvent.click(screen.getByRole('button', { name: /save view/i }))

    await waitFor(() => expect(createMock.mutateAsync).toHaveBeenCalledTimes(1))
    const payload = createMock.mutateAsync.mock.calls[0][0] as CreateViewInput
    expect(payload.team_id).toBe('t-1')
    expect(payload.name).toBe('Urgent bugs')
    expect(payload.filters).toEqual({ status_id: 'st-1', priority: 0 })
    expect(payload.group_by).toBe('status')
    expect(payload.order_by).toBe('priority')
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false))
  })

  it('does not fire the API on submit with an empty name (VAL-VIEWS-002)', () => {
    renderDialog()
    const form = screen.getByPlaceholderText('View name').closest('form')!
    act(() => {
      fireEvent.submit(form)
    })
    expect(createMock.mutateAsync).not.toHaveBeenCalled()
  })

  it('keeps the dialog open on backend error', async () => {
    createMock.mutateAsync.mockRejectedValue(new Error('boom'))
    const { onOpenChange } = renderDialog()
    typeValue(screen.getByPlaceholderText('View name'), 'Keep me')
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /save view/i })).toBeEnabled(),
    )
    fireEvent.click(screen.getByRole('button', { name: /save view/i }))

    await waitFor(() => expect(createMock.mutateAsync).toHaveBeenCalled())
    expect((screen.getByPlaceholderText('View name') as HTMLInputElement).value).toBe('Keep me')
    expect(onOpenChange).not.toHaveBeenCalled()
  })
})
