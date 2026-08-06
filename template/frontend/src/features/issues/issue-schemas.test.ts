import { describe, it, expect } from 'vitest'
import { createIssueFormSchema, ISSUE_TITLE_MAX } from './issue-schemas'

describe('createIssueFormSchema', () => {
  it('accepts a valid title', () => {
    const r = createIssueFormSchema.safeParse({ title: 'Hello', description: '' })
    expect(r.success).toBe(true)
  })

  it('rejects an empty title', () => {
    const r = createIssueFormSchema.safeParse({ title: '' })
    expect(r.success).toBe(false)
  })

  it('rejects a whitespace-only title', () => {
    const r = createIssueFormSchema.safeParse({ title: '   ' })
    expect(r.success).toBe(false)
  })

  it('trims a padded title to a valid value', () => {
    const r = createIssueFormSchema.safeParse({ title: '  Hi  ' })
    expect(r.success).toBe(true)
    if (r.success) expect(r.data.title).toBe('Hi')
  })

  it('accepts a single-character title', () => {
    const r = createIssueFormSchema.safeParse({ title: 'X' })
    expect(r.success).toBe(true)
  })

  it(`rejects a title longer than ${ISSUE_TITLE_MAX}`, () => {
    const r = createIssueFormSchema.safeParse({ title: 'A'.repeat(ISSUE_TITLE_MAX + 1) })
    expect(r.success).toBe(false)
  })

  it('makes description optional', () => {
    const r = createIssueFormSchema.safeParse({ title: 'T' })
    expect(r.success).toBe(true)
  })
})
