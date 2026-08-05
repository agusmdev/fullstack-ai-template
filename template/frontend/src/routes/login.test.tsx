import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Route } from './login'

// vi.mock factories are hoisted above the const declarations, so the mock fns
// must be created with vi.hoisted to be available when the factory runs.
const { submitMock, useAuthSubmitMock } = vi.hoisted(() => {
  const submitMock = vi.fn()
  const useAuthSubmitMock = vi.fn(() => ({ submit: submitMock, isLoading: false }))
  return { submitMock, useAuthSubmitMock }
})
vi.mock('@/hooks/useAuthSubmit', () => ({ useAuthSubmit: useAuthSubmitMock }))

describe('Login route', () => {
  beforeEach(() => {
    submitMock.mockReset()
    useAuthSubmitMock.mockClear()
    // Route.useSearch() needs a router context the unit test does not provide;
    // stub it to return the default (no redirect) search params.
    ;(Route as unknown as { useSearch: () => unknown }).useSearch = () => ({ redirect: undefined })
  })

  const Login = Route.options.component as React.FC

  it('renders the sign-in form shell', () => {
    render(<Login />)
    // "Sign in" also labels the submit button, so assert on the unique description.
    expect(screen.getByText('Enter your email and password to access your account')).toBeInTheDocument()
    expect(screen.getAllByText('Sign in').length).toBeGreaterThanOrEqual(1)
  })

  it('renders email and password fields and the submit button', () => {
    render(<Login />)
    expect(screen.getByPlaceholderText('john@example.com')).toHaveAttribute('type', 'email')
    expect(screen.getByPlaceholderText('••••••••')).toHaveAttribute('type', 'password')
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('renders a link to register', () => {
    render(<Login />)
    expect(screen.getByRole('link', { name: 'Create account' })).toHaveAttribute('href', '/register')
  })

  it('wires useAuthSubmit with the login endpoint and success/error messages', () => {
    render(<Login />)
    expect(useAuthSubmitMock).toHaveBeenCalled()
    // useForm re-renders on mount, so check the latest call's arguments.
    const lastCall = useAuthSubmitMock.mock.calls.at(-1) as unknown as [string, string, string]
    const [endpoint, successMessage, errorMessage] = lastCall
    expect(endpoint).toBe('/auth/login')
    expect(successMessage).toBe('Signed in successfully')
    expect(errorMessage).toBe('Login failed')
  })

  it('submits the form values through the submit handler', async () => {
    render(<Login />)
    fireEvent.change(screen.getByPlaceholderText('john@example.com'), {
      target: { value: 'user@example.com' },
    })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'secret123' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    await waitFor(() => {
      expect(submitMock).toHaveBeenCalledWith({ email: 'user@example.com', password: 'secret123' })
    })
  })

  it('does not submit when the email is invalid (schema validation)', async () => {
    render(<Login />)
    fireEvent.change(screen.getByPlaceholderText('john@example.com'), {
      target: { value: 'not-an-email' },
    })
    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'secret123' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    // Validation fails before submit fires.
    await waitFor(() => expect(submitMock).not.toHaveBeenCalled())
  })
})
