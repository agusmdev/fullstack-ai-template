import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { Navigation } from './Navigation'

const mockLogout = vi.fn()

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from '@/contexts/AuthContext'
const mockUseAuth = useAuth as ReturnType<typeof vi.fn>

describe('Navigation (unauthenticated)', () => {
  beforeEach(() => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, logout: mockLogout })
  })

  it('renders Login and Sign Up links', () => {
    render(<Navigation />)
    expect(screen.getByRole('link', { name: 'Login' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Sign Up' })).toBeInTheDocument()
  })

  it('does not render Logout button', () => {
    render(<Navigation />)
    expect(screen.queryByRole('button', { name: 'Logout' })).not.toBeInTheDocument()
  })

  it('does not render Items link', () => {
    render(<Navigation />)
    expect(screen.queryByRole('link', { name: 'Items' })).not.toBeInTheDocument()
  })
})

describe('Navigation (authenticated)', () => {
  beforeEach(() => {
    mockLogout.mockReset()
    mockUseAuth.mockReturnValue({ isAuthenticated: true, logout: mockLogout })
  })

  it('renders Logout button and Items link', () => {
    render(<Navigation />)
    expect(screen.getByRole('button', { name: 'Logout' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Items' })).toBeInTheDocument()
  })

  it('does not render Login or Sign Up when authenticated', () => {
    render(<Navigation />)
    expect(screen.queryByRole('link', { name: 'Login' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Sign Up' })).not.toBeInTheDocument()
  })

  it('calls logout when Logout button is clicked', () => {
    render(<Navigation />)
    fireEvent.click(screen.getByRole('button', { name: 'Logout' }))
    expect(mockLogout).toHaveBeenCalledTimes(1)
  })
})
