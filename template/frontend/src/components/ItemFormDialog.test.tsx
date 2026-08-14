import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ItemFormDialog } from './ItemFormDialog'
import type { Item } from '@/types/item'

// Spy on toastApiError so we can assert the error path without depending on toast internals.
const { toastApiError } = vi.hoisted(() => ({ toastApiError: vi.fn() }))
vi.mock('@/lib/error-handler', () => ({ toastApiError }))

const sampleItem: Item = {
  id: 'item-1',
  name: 'Widget',
  description: 'A widget',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  deleted_at: null,
  user_id: 'u1',
}

// Radix DialogTrigger asChild uses Slot to clone its child and inject onClick/ref,
// so the trigger must be a plain element (not a component that drops those props).
const openTrigger = <button type="button">Open</button>

describe('ItemFormDialog (create mode)', () => {
  it('renders the provided trigger', () => {
    const { container } = render(
      <ItemFormDialog mode="create" trigger={openTrigger} onSubmit={vi.fn()} isPending={false} />,
    )
    expect(screen.getByText('Open')).toBeInTheDocument()
    expect(container).toBeDefined()
  })

  it('shows the create dialog content when the trigger is clicked', async () => {
    render(<ItemFormDialog mode="create" trigger={openTrigger} onSubmit={vi.fn()} isPending={false} />)

    fireEvent.click(screen.getByText('Open'))

    expect(await screen.findByText('Create New Item')).toBeInTheDocument()
    expect(screen.getByText('Add a new item to your collection. Fill in the details below.')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Enter item name')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Create' })).toBeInTheDocument()
  })

  it('shows the submitting label while pending', async () => {
    render(<ItemFormDialog mode="create" trigger={openTrigger} onSubmit={vi.fn()} isPending={true} />)

    fireEvent.click(screen.getByText('Open'))

    expect(await screen.findByRole('button', { name: 'Creating...' })).toBeDisabled()
  })

  it('submits the entered name and description, then closes the dialog', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    render(<ItemFormDialog mode="create" trigger={openTrigger} onSubmit={onSubmit} isPending={false} />)

    fireEvent.click(screen.getByText('Open'))

    const nameInput = await screen.findByPlaceholderText('Enter item name')
    fireEvent.change(nameInput, { target: { value: 'My New Item' } })
    fireEvent.change(screen.getByPlaceholderText('Enter item description'), {
      target: { value: 'A description' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Create' }))

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({ name: 'My New Item', description: 'A description' })
    })
    // Successful submit closes the dialog (title disappears).
    await waitFor(() => {
      expect(screen.queryByText('Create New Item')).not.toBeInTheDocument()
    })
  })

  it('blocks submit when the name is empty (schema validation)', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    render(<ItemFormDialog mode="create" trigger={openTrigger} onSubmit={onSubmit} isPending={false} />)

    fireEvent.click(screen.getByText('Open'))
    await screen.findByPlaceholderText('Enter item name')

    fireEvent.click(screen.getByRole('button', { name: 'Create' }))

    // Validation prevents onSubmit; the dialog stays open.
    await waitFor(() => {
      expect(onSubmit).not.toHaveBeenCalled()
    })
    expect(screen.getByText('Create New Item')).toBeInTheDocument()
  })

  it('shows an error toast and keeps the dialog open when onSubmit rejects', async () => {
    toastApiError.mockClear()
    const onSubmit = vi.fn().mockRejectedValue(new Error('nope'))
    render(<ItemFormDialog mode="create" trigger={openTrigger} onSubmit={onSubmit} isPending={false} />)

    fireEvent.click(screen.getByText('Open'))
    const nameInput = await screen.findByPlaceholderText('Enter item name')
    fireEvent.change(nameInput, { target: { value: 'X' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create' }))

    await waitFor(() => expect(onSubmit).toHaveBeenCalled())
    expect(toastApiError).toHaveBeenCalledTimes(1)
    // Dialog stays open on error.
    expect(screen.getByText('Create New Item')).toBeInTheDocument()
  })
})

describe('ItemFormDialog (edit mode)', () => {
  it('pre-fills the form with the item values when opened', async () => {
    render(
      <ItemFormDialog mode="edit" item={sampleItem} trigger={openTrigger} onSubmit={vi.fn()} isPending={false} />,
    )

    fireEvent.click(screen.getByText('Open'))

    expect(await screen.findByText('Edit Item')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Enter item name')).toHaveValue('Widget')
    expect(screen.getByPlaceholderText('Enter item description')).toHaveValue('A widget')
    expect(screen.getByRole('button', { name: 'Update' })).toBeInTheDocument()
  })
})
