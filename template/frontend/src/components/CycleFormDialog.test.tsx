import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { CycleFormDialog } from './CycleFormDialog'

// Mock the create cycle hook so the test is isolated.
const createCycleMock = vi.hoisted(() => ({
  mutateAsync: vi.fn(),
  isPending: false,
}))

vi.mock('@/hooks/useCycles', () => ({
  useCreateCycle: () => createCycleMock,
}))

function renderDialog(open = true) {
  return render(
    <CycleFormDialog open={open} onOpenChange={vi.fn()} teamId="t-1" />,
  )
}

describe('CycleFormDialog', () => {
  beforeEach(() => {
    createCycleMock.mutateAsync.mockReset()
    createCycleMock.isPending = false
  })

  it('renders name, start date, and end date inputs (VAL-CYCLES-001)', () => {
    renderDialog()
    expect(screen.getByPlaceholderText('Cycle name')).toBeInTheDocument()
    expect(screen.getByLabelText('Start date')).toBeInTheDocument()
    expect(screen.getByLabelText('End date')).toBeInTheDocument()
  })

  it('disables submit until all three fields are valid', () => {
    renderDialog()
    const submit = screen.getByRole('button', { name: /create cycle/i })
    expect(submit).toBeDisabled()
  })

  it('rejects end date before start date (VAL-CYCLES-002)', async () => {
    renderDialog()

    fireEvent.change(screen.getByPlaceholderText('Cycle name'), {
      target: { value: 'Sprint 1' },
    })
    fireEvent.change(screen.getByLabelText('Start date'), {
      target: { value: '2026-08-14' },
    })
    fireEvent.change(screen.getByLabelText('End date'), {
      target: { value: '2026-08-01' },
    })
    fireEvent.click(screen.getByRole('button', { name: /create cycle/i }))

    await waitFor(() => {
      expect(
        screen.getByText('End date must be after start date'),
      ).toBeInTheDocument()
    })
    expect(createCycleMock.mutateAsync).not.toHaveBeenCalled()
  })

  it('submits with a valid window', async () => {
    createCycleMock.mutateAsync.mockResolvedValue({})
    const onOpenChange = vi.fn()
    render(
      <CycleFormDialog open onOpenChange={onOpenChange} teamId="t-1" />,
    )

    fireEvent.change(screen.getByPlaceholderText('Cycle name'), {
      target: { value: 'Sprint 1' },
    })
    fireEvent.change(screen.getByLabelText('Start date'), {
      target: { value: '2026-08-01' },
    })
    fireEvent.change(screen.getByLabelText('End date'), {
      target: { value: '2026-08-14' },
    })

    const submit = screen.getByRole('button', { name: /create cycle/i })
    await waitFor(() => expect(submit).not.toBeDisabled())
    fireEvent.click(submit)

    await waitFor(() =>
      expect(createCycleMock.mutateAsync).toHaveBeenCalledWith({
        team_id: 't-1',
        name: 'Sprint 1',
        starts_at: '2026-08-01',
        ends_at: '2026-08-14',
      }),
    )
  })
})
