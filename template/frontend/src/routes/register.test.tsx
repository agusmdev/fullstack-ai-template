import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Route } from './register'

// vi.mock factories are hoisted above the const declarations, so the mock fns
// must be created with vi.hoisted to be available when the factory runs.
const { submitMock, useAuthSubmitMock } = vi.hoisted(() => {
  const submitMock = vi.fn()
  const useAuthSubmitMock = vi.fn(() => ({ submit: submitMock, isLoading: false }))
  return { submitMock, useAuthSubmitMock }
})
vi.mock('@/hooks/useAuthSubmit', () => ({ useAuthSubmit: useAuthSubmitMock }))

describe('Register route', () => {
  beforeEach(() => {
    submitMock.mockReset()
    useAuthSubmitMock.mockClear()
  })

  const Register = Route.options.component as React.FC

  it('renders the create-account form shell', () => {
    render(<Register />)
    expect(screen.getByText('Create an account')).toBeInTheDocument()
    expect(screen.getByText('Enter your information to get started')).toBeInTheDocument()
  })

  it('renders email, password, and confirm-password fields', () => {
    render(<Register />)
    expect(screen.getByPlaceholderText('john@example.com')).toHaveAttribute('type', 'email')
    const passwordInputs = screen.getAllByPlaceholderText('••••••••')
    expect(passwordInputs).toHaveLength(2)
    expect(screen.getByText('Confirm Password')).toBeInTheDocument()
  })

  it('renders a link back to sign in', () => {
    render(<Register />)
    expect(screen.getByRole('link', { name: 'Sign in' })).toHaveAttribute('href', '/login')
  })

  it('wires useAuthSubmit with the register endpoint and success/error messages', () => {
    render(<Register />)
    expect(useAuthSubmitMock).toHaveBeenCalled()
    // useForm re-renders on mount, so check the latest call's arguments.
    const lastCall = useAuthSubmitMock.mock.calls.at(-1) as unknown as [string, string, string]
    const [endpoint, successMessage, errorMessage] = lastCall
    expect(endpoint).toBe('/auth/register')
    expect(successMessage).toBe('Account created successfully')
    expect(errorMessage).toBe('Registration failed')
  })

  it('submits the form (renamed payload) through the submit handler', async () => {
    render(<Register />)
    fireEvent.change(screen.getByPlaceholderText('john@example.com'), {
      target: { value: 'user@example.com' },
    })
    const passwordInputs = screen.getAllByPlaceholderText('••••••••')
    fireEvent.change(passwordInputs[0], { target: { value: 'Password1!' } })
    fireEvent.change(passwordInputs[1], { target: { value: 'Password1!' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))

    // registerFormToPayload rewrites password → raw_password and drops confirmPassword.
    await waitFor(() => {
      expect(submitMock).toHaveBeenCalledWith({ email: 'user@example.com', raw_password: 'Password1!' })
    })
  })

  it('does not submit when passwords do not match (schema validation)', async () => {
    render(<Register />)
    fireEvent.change(screen.getByPlaceholderText('john@example.com'), {
      target: { value: 'user@example.com' },
    })
    const passwordInputs = screen.getAllByPlaceholderText('••••••••')
    fireEvent.change(passwordInputs[0], { target: { value: 'Password1!' } })
    fireEvent.change(passwordInputs[1], { target: { value: 'Different1!' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))

    await waitFor(() => expect(submitMock).not.toHaveBeenCalled())
  })
})
