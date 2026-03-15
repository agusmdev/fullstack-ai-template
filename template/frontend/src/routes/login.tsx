import { createFileRoute, Link } from '@tanstack/react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '@/components/ui/button'
import { Form } from '@/components/ui/form'
import { AuthFormShell } from '@/components/AuthFormShell'
import { EmailField, PasswordField } from '@/components/AuthFormFields'
import { API } from '@/lib/api-endpoints'
import { useAuthSubmit } from '@/hooks/useAuthSubmit'
import { loginSchema, type LoginFormData } from '@/lib/schemas'

export const Route = createFileRoute('/login')({
  component: Login,
})

function Login() {
  const { submit, isLoading } = useAuthSubmit(API.AUTH.LOGIN, 'Signed in successfully', 'Login failed')

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const onSubmit = (data: LoginFormData) =>
    submit({ email: data.email, password: data.password })

  return (
    <AuthFormShell
      title="Sign in"
      description="Enter your email and password to access your account"
      footer={
        <div className="mt-4 text-center text-sm text-muted-foreground">
          Don't have an account?{' '}
          <Link to="/register" className="text-primary hover:text-primary/80 underline-offset-4 hover:underline">
            Create account
          </Link>
        </div>
      }
    >
      <Form {...form}>
        <form method="post" action="#" onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <EmailField control={form.control} name="email" isLoading={isLoading} />
          <PasswordField control={form.control} name="password" isLoading={isLoading} />
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>
      </Form>
    </AuthFormShell>
  )
}
