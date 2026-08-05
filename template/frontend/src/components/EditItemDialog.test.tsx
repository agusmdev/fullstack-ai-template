import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { EditItemDialog } from './EditItemDialog'
import type { Item } from '@/types/item'

const updateItemMutate = vi.hoisted(() => vi.fn())
vi.mock('@/hooks/useItems', () => ({
  useUpdateItem: () => ({
    mutateAsync: updateItemMutate,
    isPending: false,
  }),
}))

const item: Item = {
  id: 'item-9',
  name: 'Old Name',
  description: 'old desc',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  deleted_at: null,
  user_id: 'u1',
}

function Wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return React.createElement(QueryClientProvider, { client: qc }, children)
}

describe('EditItemDialog', () => {
  beforeEach(() => updateItemMutate.mockReset())

  it('pre-fills the form with the existing item values when opened', async () => {
    render(
      <Wrapper>
        <EditItemDialog item={item} trigger={<button type="button">Edit</button>} />
      </Wrapper>,
    )

    fireEvent.click(screen.getByText('Edit'))
    expect(await screen.findByPlaceholderText('Enter item name')).toHaveValue('Old Name')
    expect(screen.getByPlaceholderText('Enter item description')).toHaveValue('old desc')
  })

  it('updates the item via the mutation with the edited values', async () => {
    updateItemMutate.mockResolvedValue(undefined)
    render(
      <Wrapper>
        <EditItemDialog item={item} trigger={<button type="button">Edit</button>} />
      </Wrapper>,
    )

    fireEvent.click(screen.getByText('Edit'))
    const name = await screen.findByPlaceholderText('Enter item name')
    fireEvent.change(name, { target: { value: 'New Name' } })
    fireEvent.click(screen.getByRole('button', { name: 'Update' }))

    await waitFor(() => {
      expect(updateItemMutate).toHaveBeenCalledWith({ name: 'New Name', description: 'old desc' })
    })
  })
})
