import { describe, it, expect } from 'vitest'
import { itemSchema, itemFormToPayload } from './item-schemas'

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
