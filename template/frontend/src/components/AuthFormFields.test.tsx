import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FormProvider, useForm } from 'react-hook-form'
import { EmailField, PasswordField } from './AuthFormFields'

interface FormValues {
  email: string
  password: string
}

// EmailField/PasswordField rely on react-hook-form context (FormLabel/FormMessage
// read from useFormContext), so we wrap them in a FormProvider harness. useForm
// must be called from within a React render.
function Harness({
  isLoading,
  label,
  field = 'email',
}: {
  isLoading: boolean
  label?: string
  field?: 'email' | 'password'
}) {
  const form = useForm<FormValues>({ defaultValues: { email: '', password: '' } })
  return (
    <FormProvider {...form}>
      {field === 'email' ? (
        <EmailField control={form.control} name="email" isLoading={isLoading} />
      ) : (
        <PasswordField
          control={form.control}
          name="password"
          isLoading={isLoading}
          label={label}
        />
      )}
    </FormProvider>
  )
}

describe('EmailField', () => {
  it('renders a labeled email input', () => {
    render(<Harness isLoading={false} field="email" />)

    expect(screen.getByText('Email')).toBeInTheDocument()
    const input = screen.getByPlaceholderText('john@example.com')
    expect(input).toHaveAttribute('type', 'email')
    expect(input).not.toBeDisabled()
  })

  it('disables the input when isLoading is true', () => {
    render(<Harness isLoading={true} field="email" />)

    expect(screen.getByPlaceholderText('john@example.com')).toBeDisabled()
  })
})

describe('PasswordField', () => {
  it('renders a password input with the default label', () => {
    render(<Harness isLoading={false} field="password" />)

    expect(screen.getByText('Password')).toBeInTheDocument()
    const input = screen.getByPlaceholderText('••••••••')
    expect(input).toHaveAttribute('type', 'password')
    expect(input).not.toBeDisabled()
  })

  it('renders a custom label when provided', () => {
    render(<Harness isLoading={false} field="password" label="Confirm Password" />)

    expect(screen.getByText('Confirm Password')).toBeInTheDocument()
  })

  it('disables the input when isLoading is true', () => {
    render(<Harness isLoading={true} field="password" />)

    expect(screen.getByPlaceholderText('••••••••')).toBeDisabled()
  })
})
