import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { UserMenu } from './UserMenu'

const navigateMock = vi.fn()
const logoutMock = vi.fn()
const apiMock = vi.hoisted(() => ({ get: vi.fn() }))
const authMock = vi.hoisted(() => ({ isAuthenticated: vi.fn() }))

vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => navigateMock,
}))
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ logout: logoutMock }),
}))
vi.mock('@/lib/api-client', () => ({ api: apiMock }))
vi.mock('@/lib/auth', () => ({
  isAuthenticated: authMock.isAuthenticated,
}))

const mockUser = {
  id: 'u-1',
  email: 'jane@example.com',
  display_name: 'Jane',
  email_verified_at: null,
  is_email_verified: false,
}

function wrapper(qc: QueryClient) {
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children)
}

describe('UserMenu', () => {
  beforeEach(() => {
    navigateMock.mockReset()
    logoutMock.mockReset()
    apiMock.get.mockReset()
    authMock.isAuthenticated.mockReset()
    authMock.isAuthenticated.mockReturnValue(true)
  })

  it('renders an avatar button with the user initials', async () => {
    apiMock.get.mockResolvedValue(mockUser)
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(<UserMenu />, { wrapper: wrapper(qc) })
    await waitFor(() => {
      expect(screen.getByText('JA')).toBeInTheDocument()
    })
  })

  it('opens the menu and shows email + logout', async () => {
    apiMock.get.mockResolvedValue(mockUser)
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(<UserMenu />, { wrapper: wrapper(qc) })
    // Wait for the user query to resolve so the email is available
    await screen.findByText('JA')
    fireEvent.click(screen.getByLabelText('User menu'))
    expect(screen.getByText('jane@example.com')).toBeInTheDocument()
    expect(screen.getByText('Log out')).toBeInTheDocument()
  })

  it('calls logout when Log out is clicked', async () => {
    apiMock.get.mockResolvedValue(mockUser)
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(<UserMenu />, { wrapper: wrapper(qc) })
    await waitFor(() => expect(apiMock.get).toHaveBeenCalled())
    fireEvent.click(screen.getByLabelText('User menu'))
    fireEvent.click(screen.getByText('Log out'))
    expect(logoutMock).toHaveBeenCalledTimes(1)
  })

  it('navigates to settings when teamKey is provided', async () => {
    apiMock.get.mockResolvedValue(mockUser)
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(<UserMenu teamKey="ENG" />, { wrapper: wrapper(qc) })
    await waitFor(() => expect(apiMock.get).toHaveBeenCalled())
    fireEvent.click(screen.getByLabelText('User menu'))
    fireEvent.click(screen.getByText('Settings'))
    expect(navigateMock).toHaveBeenCalledWith({
      to: '/$team/settings',
      params: { team: 'ENG' },
    })
  })
})
