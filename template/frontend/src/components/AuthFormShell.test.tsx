import { render, screen } from '@testing-library/react'
import { AuthFormShell } from './AuthFormShell'

describe('AuthFormShell', () => {
  it('renders title and description', () => {
    render(
      <AuthFormShell title="Sign In" description="Enter your credentials" footer={null}>
        <div>form content</div>
      </AuthFormShell>
    )

    expect(screen.getByText('Sign In')).toBeInTheDocument()
    expect(screen.getByText('Enter your credentials')).toBeInTheDocument()
  })

  it('renders children', () => {
    render(
      <AuthFormShell title="Title" description="Desc" footer={null}>
        <input data-testid="form-input" />
      </AuthFormShell>
    )

    expect(screen.getByTestId('form-input')).toBeInTheDocument()
  })

  it('renders footer slot', () => {
    render(
      <AuthFormShell
        title="Title"
        description="Desc"
        footer={<a href="/register">Create account</a>}
      >
        <div />
      </AuthFormShell>
    )

    expect(screen.getByRole('link', { name: 'Create account' })).toBeInTheDocument()
  })
})
