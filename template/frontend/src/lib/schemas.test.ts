import { describe, it, expect } from 'vitest'
import {
  loginSchema, registerSchema, itemSchema,
  registerFormToPayload, itemFormToPayload,
} from './schemas'

describe('loginSchema', () => {
  it('accepts valid credentials', () => {
    const result = loginSchema.safeParse({ email: 'user@example.com', password: 'secret' })
    expect(result.success).toBe(true)
  })

  it('rejects invalid email', () => {
    const result = loginSchema.safeParse({ email: 'not-an-email', password: 'secret' })
    expect(result.success).toBe(false)
  })

  it('rejects empty password', () => {
    const result = loginSchema.safeParse({ email: 'user@example.com', password: '' })
    expect(result.success).toBe(false)
  })
})

describe('registerSchema', () => {
  it('accepts valid registration with matching passwords', () => {
    const result = registerSchema.safeParse({
      email: 'user@example.com',
      password: 'Password1!',
      confirmPassword: 'Password1!',
    })
    expect(result.success).toBe(true)
  })

  it('rejects mismatched passwords', () => {
    const result = registerSchema.safeParse({
      email: 'user@example.com',
      password: 'Password1!',
      confirmPassword: 'Different1!',
    })
    expect(result.success).toBe(false)
    if (!result.success) {
      const confirmError = result.error.issues.find(i => i.path.includes('confirmPassword'))
      expect(confirmError?.message).toBe("Passwords don't match")
    }
  })

  it('rejects password shorter than 8 characters', () => {
    const result = registerSchema.safeParse({
      email: 'user@example.com',
      password: 'short',
      confirmPassword: 'short',
    })
    expect(result.success).toBe(false)
  })

  it('rejects invalid email', () => {
    const result = registerSchema.safeParse({
      email: 'bad',
      password: 'Password1!',
      confirmPassword: 'Password1!',
    })
    expect(result.success).toBe(false)
  })
})

describe('itemSchema', () => {
  it('accepts valid item with name only', () => {
    const result = itemSchema.safeParse({ name: 'My Item' })
    expect(result.success).toBe(true)
  })

  it('accepts valid item with name and description', () => {
    const result = itemSchema.safeParse({ name: 'My Item', description: 'A description' })
    expect(result.success).toBe(true)
  })

  it('rejects empty name', () => {
    const result = itemSchema.safeParse({ name: '' })
    expect(result.success).toBe(false)
  })

  it('rejects name longer than 255 characters', () => {
    const result = itemSchema.safeParse({ name: 'a'.repeat(256) })
    expect(result.success).toBe(false)
  })

  it('rejects description longer than 5000 characters', () => {
    const result = itemSchema.safeParse({ name: 'Valid', description: 'x'.repeat(5001) })
    expect(result.success).toBe(false)
  })
})

describe('registerFormToPayload', () => {
  it('renames password → raw_password for register API shape', () => {
    const result = registerFormToPayload({ email: 'user@example.com', password: 'Password1!', confirmPassword: 'Password1!' })
    expect(result).toEqual({ email: 'user@example.com', raw_password: 'Password1!' })
  })

  it('omits confirmPassword from payload', () => {
    const result = registerFormToPayload({ email: 'user@example.com', password: 'Password1!', confirmPassword: 'Password1!' })
    expect(result).not.toHaveProperty('confirmPassword')
  })
})

describe('itemFormToPayload', () => {
  it('passes name and description through', () => {
    const result = itemFormToPayload({ name: 'My Item', description: 'A description' })
    expect(result).toEqual({ name: 'My Item', description: 'A description' })
  })

  it('omits description when empty string', () => {
    const result = itemFormToPayload({ name: 'My Item', description: '' })
    expect(result.description).toBeUndefined()
  })
})
