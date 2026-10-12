import { createFileRoute, Link } from '@tanstack/react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '@/components/ui/button'
import { Form } from '@/components/ui/form'
import { AuthFormShell } from '@/components/AuthFormShell'
import { EmailField, PasswordField } from '@/components/AuthFormFields'
import { API } from '@/lib/api-endpoints'
import { useAuthSubmit } from '@/hooks/useAuthSubmit'
import { useHydrated } from '@/hooks/useHydrated'
import { loginSchema, type LoginFormData } from '@/features/auth/auth-schemas'

/** Only an in-app path ('/items'), never a URL or '//host': anything else goes home after sign-in. */
function safeRedirect(value: unknown): string | undefined {
  if (typeof value !== 'string' || !value.startsWith('/') || value.startsWith('//'))
    return undefined
  return value.includes('\\') ? undefined : value
}

export const Route = createFileRoute('/login')({
  validateSearch: (search: Record<string, unknown>): { redirect?: string } => ({
    redirect: safeRedirect(search['redirect']),
  }),
  component: Login,
})

function Login() {
  const { redirect: redirectTo } = Route.useSearch()
  const hydrated = useHydrated()
  const { submit, isLoading } = useAuthSubmit<LoginFormData>(
    API.AUTH.LOGIN,
    'Signed in successfully',
    'Login failed',
    { to: (redirectTo ?? '/') as '/' }
  )

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  // Inert until hydrated, and while the request runs.
  const disabled = isLoading || !hydrated

  const onSubmit = (data: LoginFormData) => submit(data)

  return (
    <AuthFormShell
      title="Sign in"
      description="Enter your email and password to access your account"
      footer={
        <div className="mt-4 text-center text-sm text-muted-foreground">
          Don&apos;t have an account?{' '}
          <Link
            to="/register"
            className="text-primary hover:text-primary/80 underline-offset-4 hover:underline"
          >
            Create account
          </Link>
        </div>
      }
    >
      <Form {...form}>
        {/* noValidate: the zod schema validates, so its messages show instead of the browser's. */}
        <form
          method="post"
          action="#"
          noValidate
          onSubmit={form.handleSubmit(onSubmit)}
          className="space-y-4"
        >
          <EmailField control={form.control} name="email" disabled={disabled} />
          <PasswordField control={form.control} name="password" disabled={disabled} />
          <Button type="submit" className="w-full" disabled={disabled}>
            {isLoading ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>
      </Form>
    </AuthFormShell>
  )
}
