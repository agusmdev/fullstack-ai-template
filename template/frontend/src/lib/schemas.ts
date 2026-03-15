import { z } from 'zod'

// Auth schemas
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

// Item schemas
export const itemSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255, 'Name must be less than 255 characters'),
  description: z.string().max(5000, 'Description must be less than 5000 characters').optional(),
})

// Exported types
export type LoginFormData = z.infer<typeof loginSchema>
export type RegisterFormData = z.infer<typeof registerSchema>
export type ItemFormData = z.infer<typeof itemSchema>

/** Maps form values to the mutation payload shape expected by item API hooks. */
export function itemFormToPayload(data: ItemFormData) {
  return { name: data.name, description: data.description || undefined }
}

/** Maps register form values to the API payload (renames password → raw_password per backend contract). */
export function registerFormToPayload(data: RegisterFormData) {
  return { email: data.email, raw_password: data.password }
}

export type RegisterPayload = ReturnType<typeof registerFormToPayload>
