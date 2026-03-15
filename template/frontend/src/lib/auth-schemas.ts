import { z } from 'zod'

export const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
})

export const registerSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
})

export type LoginFormData = z.infer<typeof loginSchema>
export type RegisterFormData = z.infer<typeof registerSchema>

/** Maps register form values to the API payload (renames password → raw_password per backend contract). */
export function registerFormToPayload(data: RegisterFormData) {
  return { email: data.email, raw_password: data.password }
}

export type RegisterPayload = ReturnType<typeof registerFormToPayload>
