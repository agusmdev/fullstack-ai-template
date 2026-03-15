import { describe, it, expect } from 'vitest'
import { ApiError } from './api-client'

describe('ApiError', () => {
  it('creates error with status and message', () => {
    const err = new ApiError(404, 'Not found')
    expect(err.status).toBe(404)
    expect(err.message).toBe('Not found')
    expect(err.name).toBe('ApiError')
  })

  it('stores optional code', () => {
    const err = new ApiError(422, 'Validation failed', 'validation_error')
    expect(err.code).toBe('validation_error')
  })

  it('stores optional fields', () => {
    const fields = { email: ['Invalid email'], password: ['Too short'] }
    const err = new ApiError(422, 'Validation failed', 'validation_error', fields)
    expect(err.fields).toEqual(fields)
  })

  it('is instance of Error', () => {
    const err = new ApiError(500, 'Server error')
    expect(err instanceof Error).toBe(true)
  })

  it('is instance of ApiError', () => {
    const err = new ApiError(401, 'Unauthorized')
    expect(err instanceof ApiError).toBe(true)
  })

  it('has undefined code when not provided', () => {
    const err = new ApiError(404, 'Not found')
    expect(err.code).toBeUndefined()
  })

  it('has undefined fields when not provided', () => {
    const err = new ApiError(404, 'Not found')
    expect(err.fields).toBeUndefined()
  })
})
