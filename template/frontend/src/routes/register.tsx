import { createFileRoute, Link } from '@tanstack/react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '@/components/ui/button'
import { Form } from '@/components/ui/form'
import { AuthFormShell } from '@/components/AuthFormShell'
import { EmailField, PasswordField } from '@/components/AuthFormFields'
import { API } from '@/lib/api-endpoints'
import { useAuthSubmit } from '@/hooks/useAuthSubmit'
import { registerSchema, registerFormToPayload, type RegisterFormData, type RegisterPayload } from '@/lib/auth-schemas'

export const Route = createFileRoute('/register')({
  component: Register,
})

function Register() {
  const { submit, isLoading } = useAuthSubmit<RegisterPayload>(
    API.AUTH.REGISTER,
    'Account created successfully',
    'Registration failed',
  )

  const form = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: '', password: '', confirmPassword: '' },
  })

  const onSubmit = (data: RegisterFormData) =>
    submit(registerFormToPayload(data))

  return (
    <AuthFormShell
      title="Create an account"
      description="Enter your information to get started"
      footer={
        <div className="mt-4 text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link to="/login" className="text-primary hover:text-primary/80 underline-offset-4 hover:underline">
            Sign in
          </Link>
        </div>
      }
    >
      <Form {...form}>
        <form method="post" action="#" onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <EmailField control={form.control} name="email" isLoading={isLoading} />
          <PasswordField control={form.control} name="password" isLoading={isLoading} />
          <PasswordField
            control={form.control}
            name="confirmPassword"
            isLoading={isLoading}
            label="Confirm Password"
          />
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Creating account...' : 'Create account'}
          </Button>
        </form>
      </Form>
    </AuthFormShell>
  )
}
