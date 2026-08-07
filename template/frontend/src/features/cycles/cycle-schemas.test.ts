import { describe, it, expect } from 'vitest'
import {
  createCycleFormSchema,
  defaultCreateCycleFormValues,
} from './cycle-schemas'

describe('createCycleFormSchema', () => {
  it('requires a non-empty name (VAL-CYCLES-001)', () => {
    const result = createCycleFormSchema.safeParse({
      name: '',
      starts_at: '2026-08-01',
      ends_at: '2026-08-14',
    })
    expect(result.success).toBe(false)
  })

  it('rejects whitespace-only name', () => {
    const result = createCycleFormSchema.safeParse({
      name: '   ',
      starts_at: '2026-08-01',
      ends_at: '2026-08-14',
    })
    expect(result.success).toBe(false)
  })

  it('requires start date (VAL-CYCLES-001)', () => {
    const result = createCycleFormSchema.safeParse({
      name: 'Sprint',
      starts_at: '',
      ends_at: '2026-08-14',
    })
    expect(result.success).toBe(false)
  })

  it('requires end date (VAL-CYCLES-001)', () => {
    const result = createCycleFormSchema.safeParse({
      name: 'Sprint',
      starts_at: '2026-08-01',
      ends_at: '',
    })
    expect(result.success).toBe(false)
  })

  it('rejects end before start (VAL-CYCLES-002)', () => {
    const result = createCycleFormSchema.safeParse({
      name: 'Sprint',
      starts_at: '2026-08-14',
      ends_at: '2026-08-01',
    })
    expect(result.success).toBe(false)
  })

  it('rejects end equal to start', () => {
    const result = createCycleFormSchema.safeParse({
      name: 'Sprint',
      starts_at: '2026-08-01',
      ends_at: '2026-08-01',
    })
    expect(result.success).toBe(false)
  })

  it('accepts a valid cycle', () => {
    const result = createCycleFormSchema.safeParse({
      name: 'Sprint 1',
      starts_at: '2026-08-01',
      ends_at: '2026-08-14',
    })
    expect(result.success).toBe(true)
  })
})

describe('defaultCreateCycleFormValues', () => {
  it('returns empty defaults', () => {
    expect(defaultCreateCycleFormValues()).toEqual({
      name: '',
      starts_at: '',
      ends_at: '',
    })
  })
})
