import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { AuthFormShell } from '@/components/AuthFormShell'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { useAuth } from '@/contexts/AuthContext'
import { handleApiError } from '@/lib/error-handler'
import { loginSchema, type LoginFormData } from '@/lib/schemas'
import type { AuthSessionResponse } from '@/types/auth'

export const Route = createFileRoute('/login')({
  component: Login,
})

function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [isLoading, setIsLoading] = useState(false)

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  })

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true)

    try {
      const result = await api.post<AuthSessionResponse>(API.AUTH.LOGIN, {
        email: data.email,
        password: data.password,
      })

      if (!result.id) {
        throw new Error('No session token returned from server')
      }
      login(result.id)

      toast.success('Signed in successfully')
      navigate({ to: '/' })
    } catch (err) {
      handleApiError(err, 'Login failed')
    } finally {
      setIsLoading(false)
    }
  }

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
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-muted-foreground">Email</FormLabel>
                <FormControl>
                  <Input
                    type="email"
                    placeholder="john@example.com"
                    {...field}
                    disabled={isLoading}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-muted-foreground">Password</FormLabel>
                <FormControl>
                  <Input
                    type="password"
                    placeholder="••••••••"
                    {...field}
                    disabled={isLoading}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>
      </Form>
    </AuthFormShell>
  )
}
