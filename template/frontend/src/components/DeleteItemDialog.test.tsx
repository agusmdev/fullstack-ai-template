import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DeleteItemDialog } from './DeleteItemDialog'
import type { Item } from '@/types/item'

const deleteItemMutate = vi.hoisted(() => vi.fn())
vi.mock('@/hooks/useItems', () => ({
  useDeleteItem: () => ({
    mutateAsync: deleteItemMutate,
    isPending: false,
  }),
}))

const { toastApiError } = vi.hoisted(() => ({ toastApiError: vi.fn() }))
vi.mock('@/lib/error-handler', () => ({ toastApiError }))

const item: Item = {
  id: 'item-3',
  name: 'Doomed',
  description: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  deleted_at: null,
  user_id: 'u1',
}

function Wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return React.createElement(QueryClientProvider, { client: qc }, children)
}

describe('DeleteItemDialog', () => {
  beforeEach(() => {
    deleteItemMutate.mockReset()
    toastApiError.mockReset()
  })

  it('renders the trigger', () => {
    render(
      <Wrapper>
        <DeleteItemDialog item={item} trigger={<button type="button">Delete</button>} />
      </Wrapper>,
    )
    expect(screen.getByText('Delete')).toBeInTheDocument()
  })

  it('shows the item name in the confirmation message when opened', async () => {
    render(
      <Wrapper>
        <DeleteItemDialog item={item} trigger={<button type="button">Delete</button>} />
      </Wrapper>,
    )

    fireEvent.click(screen.getByText('Delete'))
    expect(await screen.findByText(/Are you sure you want to delete "Doomed"/)).toBeInTheDocument()
  })

  it('calls the delete mutation and closes on confirm', async () => {
    deleteItemMutate.mockResolvedValue(undefined)
    render(
      <Wrapper>
        <DeleteItemDialog item={item} trigger={<button type="button">Delete</button>} />
      </Wrapper>,
    )

    fireEvent.click(screen.getByText('Delete'))
    await screen.findByText(/Are you sure you want to delete "Doomed"/)
    // Two buttons are labelled "Delete" once open: the trigger and the confirm action.
    const deleteButtons = screen.getAllByRole('button', { name: 'Delete' })
    fireEvent.click(deleteButtons[deleteButtons.length - 1])

    await waitFor(() => expect(deleteItemMutate).toHaveBeenCalledTimes(1))
    // Successful delete closes the dialog.
    await waitFor(() => {
      expect(screen.queryByText(/Are you sure/)).not.toBeInTheDocument()
    })
  })

  it('shows an error toast and stays open when the delete fails', async () => {
    deleteItemMutate.mockRejectedValue(new Error('server'))
    render(
      <Wrapper>
        <DeleteItemDialog item={item} trigger={<button type="button">Delete</button>} />
      </Wrapper>,
    )

    fireEvent.click(screen.getByText('Delete'))
    await screen.findByText(/Are you sure you want to delete "Doomed"/)
    const deleteButtons = screen.getAllByRole('button', { name: 'Delete' })
    fireEvent.click(deleteButtons[deleteButtons.length - 1])

    await waitFor(() => expect(toastApiError).toHaveBeenCalledTimes(1))
    expect(toastApiError.mock.calls[0][1]).toBe('Failed to delete item')
    // Dialog stays open on error.
    expect(screen.getByText(/Are you sure/)).toBeInTheDocument()
  })
})
