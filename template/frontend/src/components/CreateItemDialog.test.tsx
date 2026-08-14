import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CreateItemDialog } from './CreateItemDialog'

// Mock the items hook so we control the mutation without hitting the network.
const createItemMutate = vi.hoisted(() => vi.fn())
vi.mock('@/hooks/useItems', () => ({
  useCreateItem: () => ({
    mutateAsync: createItemMutate,
    isPending: false,
  }),
}))

function Wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return React.createElement(QueryClientProvider, { client: qc }, children)
}

describe('CreateItemDialog', () => {
  beforeEach(() => createItemMutate.mockReset())

  it('renders the trigger', () => {
    render(
      <Wrapper>
        <CreateItemDialog trigger={<button type="button">New</button>} />
      </Wrapper>,
    )
    expect(screen.getByText('New')).toBeInTheDocument()
  })

  it('creates an item via the mutation when the form is submitted', async () => {
    createItemMutate.mockResolvedValue(undefined)
    render(
      <Wrapper>
        <CreateItemDialog trigger={<button type="button">New</button>} />
      </Wrapper>,
    )

    fireEvent.click(screen.getByText('New'))
    const name = await screen.findByPlaceholderText('Enter item name')
    fireEvent.change(name, { target: { value: 'Created Item' } })
    fireEvent.change(screen.getByPlaceholderText('Enter item description'), {
      target: { value: 'desc' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Create' }))

    await waitFor(() => {
      expect(createItemMutate).toHaveBeenCalledWith({ name: 'Created Item', description: 'desc' })
    })
  })
})
