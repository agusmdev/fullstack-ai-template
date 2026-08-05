import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Route } from './items'
import type { Item, ItemsResponse } from '@/types/item'

// Mock the data + collaborator hooks so the route module is exercised in isolation.
// The route's own logic under test: loading/error/empty/populated rendering, search
// input wiring, pagination controls, and the formatDate helper.
const useItemsMock = vi.hoisted(() => vi.fn())
const useDebounceMock = vi.hoisted(() => vi.fn((value: string) => value))

vi.mock('@/hooks/useItems', () => ({ useItems: useItemsMock }))
vi.mock('@/hooks/useDebounce', () => ({ useDebounce: useDebounceMock }))
// Render dialogs as inert triggers so we assert they mount without pulling in
// mutation/query machinery irrelevant to the route's own behavior.
vi.mock('@/components/CreateItemDialog', () => ({
  CreateItemDialog: ({ trigger }: { trigger: React.ReactNode }) => <>{trigger}</>,
}))
vi.mock('@/components/EditItemDialog', () => ({
  EditItemDialog: ({ trigger }: { trigger: React.ReactNode }) => <>{trigger}</>,
}))
vi.mock('@/components/DeleteItemDialog', () => ({
  DeleteItemDialog: ({ trigger }: { trigger: React.ReactNode }) => <>{trigger}</>,
}))

function makeItem(overrides: Partial<Item> = {}): Item {
  return {
    id: 'item-1',
    name: 'First Item',
    description: 'A description',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    deleted_at: null,
    user_id: 'user-1',
    ...overrides,
  }
}

function renderRoute() {
  const Items = Route.options.component as React.FC
  return render(<Items />)
}

describe('Items route', () => {
  beforeEach(() => {
    useItemsMock.mockReset()
    useDebounceMock.mockReset()
    useDebounceMock.mockImplementation((value: string) => value)
  })

  it('renders the loading state while items are being fetched', () => {
    useItemsMock.mockReturnValue({ data: undefined, isLoading: true, isError: false, error: null })

    renderRoute()

    expect(screen.getByText('Loading items...')).toBeInTheDocument()
  })

  it('renders the error state with the surfaced error message', () => {
    useItemsMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error('Something broke'),
    })

    renderRoute()

    expect(screen.getByText('Error loading items')).toBeInTheDocument()
    expect(screen.getByText('Something broke')).toBeInTheDocument()
  })

  it('falls back to a generic message when the error is not an Error instance', () => {
    useItemsMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: 'string failure',
    })

    renderRoute()

    expect(screen.getByText('An unknown error occurred')).toBeInTheDocument()
  })

  it('renders the empty state when there are no items', () => {
    useItemsMock.mockReturnValue({
      data: { items: [], total: 0, pages: 1 } as ItemsResponse,
      isLoading: false,
      isError: false,
      error: null,
    })

    renderRoute()

    expect(screen.getByText('No items yet')).toBeInTheDocument()
    expect(screen.getByText('Get started by creating your first item.')).toBeInTheDocument()
    expect(screen.getByText('No items found')).toBeInTheDocument()
  })

  it('renders item cards with name, description, and formatted dates', () => {
    useItemsMock.mockReturnValue({
      data: {
        items: [makeItem()],
        total: 1,
        pages: 1,
      } as ItemsResponse,
      isLoading: false,
      isError: false,
      error: null,
    })

    renderRoute()

    expect(screen.getByText('First Item')).toBeInTheDocument()
    expect(screen.getByText('A description')).toBeInTheDocument()
    // formatDate uses toLocaleDateString(); assert the day/month appears.
    expect(screen.getByText(/Created:/)).toBeInTheDocument()
    expect(screen.queryByText(/Updated:/)).not.toBeInTheDocument()
  })

  it('shows the updated date only when it differs from the created date', () => {
    useItemsMock.mockReturnValue({
      data: {
        items: [makeItem({ updated_at: '2024-02-20T10:00:00Z' })],
        total: 1,
        pages: 1,
      } as ItemsResponse,
      isLoading: false,
      isError: false,
      error: null,
    })

    renderRoute()

    expect(screen.getByText(/Created:/)).toBeInTheDocument()
    expect(screen.getByText(/Updated:/)).toBeInTheDocument()
  })

  it('renders the Create Item trigger and total count', () => {
    useItemsMock.mockReturnValue({
      data: { items: [makeItem()], total: 1, pages: 1 } as ItemsResponse,
      isLoading: false,
      isError: false,
      error: null,
    })

    renderRoute()

    expect(screen.getByRole('button', { name: 'Create Item' })).toBeInTheDocument()
    expect(screen.getByText('1 item total')).toBeInTheDocument()
  })

  it('updates the search input and debounces it into the query params', async () => {
    useItemsMock.mockReturnValue({
      data: { items: [], total: 0, pages: 1 } as ItemsResponse,
      isLoading: false,
      isError: false,
      error: null,
    })

    renderRoute()
    const input = screen.getByPlaceholderText('Search items by name...') as HTMLInputElement

    fireEvent.change(input, { target: { value: 'widget' } })

    expect(input.value).toBe('widget')
    expect(useDebounceMock).toHaveBeenCalledWith('widget', 300)
    // useItems should be called with the (debounced) name filter applied.
    await waitFor(() => {
      const lastCall = useItemsMock.mock.calls.at(-1)?.[0]
      expect(lastCall).toMatchObject({ name: 'widget', page: 1, size: 9 })
    })
  })

  it('shows and clears the search via the Clear button', () => {
    useItemsMock.mockReturnValue({
      data: { items: [], total: 0, pages: 1 } as ItemsResponse,
      isLoading: false,
      isError: false,
      error: null,
    })

    renderRoute()
    const input = screen.getByPlaceholderText('Search items by name...') as HTMLInputElement

    fireEvent.change(input, { target: { value: 'widget' } })
    expect(screen.getByRole('button', { name: 'Clear' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Clear' }))

    expect(input.value).toBe('')
  })

  it('renders pagination controls and reflects the current page of a multi-page result', () => {
    useItemsMock.mockReturnValue({
      data: { items: [makeItem()], total: 30, pages: 4 } as ItemsResponse,
      isLoading: false,
      isError: false,
      error: null,
    })

    renderRoute()

    expect(screen.getByText('Page 1 of 4')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Go to previous page' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Go to next page' })).toBeEnabled()
  })

  it('advances to and retreats from the next page via the pagination buttons', async () => {
    useItemsMock.mockReturnValue({
      data: { items: [makeItem()], total: 30, pages: 4 } as ItemsResponse,
      isLoading: false,
      isError: false,
      error: null,
    })

    renderRoute()

    fireEvent.click(screen.getByRole('button', { name: 'Go to next page' }))
    await waitFor(() => {
      const lastCall = useItemsMock.mock.calls.at(-1)?.[0]
      expect(lastCall).toMatchObject({ page: 2 })
    })
    expect(screen.getByText('Page 2 of 4')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Go to previous page' }))
    await waitFor(() => {
      const lastCall = useItemsMock.mock.calls.at(-1)?.[0]
      expect(lastCall).toMatchObject({ page: 1 })
    })
    expect(screen.getByText('Page 1 of 4')).toBeInTheDocument()
  })
})
