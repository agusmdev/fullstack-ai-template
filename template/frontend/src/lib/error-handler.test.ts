import { describe, it, expect, vi, beforeEach } from 'vitest'
import { toastApiError, getErrorMessage } from './error-handler'
import { ApiError } from './api-client'

vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
  },
}))

import { toast } from 'sonner'

describe('toastApiError', () => {
  beforeEach(() => {
    vi.mocked(toast.error).mockClear()
  })

  it('shows one toast per field when ApiError has field errors', () => {
    const err = new ApiError(422, 'Validation failed', 'validation_error', {
      email: ['Invalid email'],
      password: ['Too short', 'Must contain a number'],
    })

    toastApiError(err, 'Save failed')

    expect(toast.error).toHaveBeenCalledTimes(2)
    expect(toast.error).toHaveBeenCalledWith('email: Invalid email')
    expect(toast.error).toHaveBeenCalledWith('password: Too short, Must contain a number')
  })

  it('shows fallback message with error description when ApiError has no fields', () => {
    const err = new ApiError(500, 'Internal server error')

    toastApiError(err, 'Request failed')

    expect(toast.error).toHaveBeenCalledTimes(1)
    expect(toast.error).toHaveBeenCalledWith('Request failed', {
      description: 'Internal server error',
    })
  })

  it('shows fallback message with Error.message for plain Error', () => {
    const err = new Error('Network timeout')

    toastApiError(err, 'Connection failed')

    expect(toast.error).toHaveBeenCalledTimes(1)
    expect(toast.error).toHaveBeenCalledWith('Connection failed', {
      description: 'Network timeout',
    })
  })

  it('shows generic description for non-Error thrown values', () => {
    toastApiError('something went wrong', 'Unexpected failure')

    expect(toast.error).toHaveBeenCalledTimes(1)
    expect(toast.error).toHaveBeenCalledWith('Unexpected failure', {
      description: 'An unexpected error occurred',
    })
  })
})

describe('getErrorMessage', () => {
  it('returns the message of an Error instance', () => {
    expect(getErrorMessage(new Error('boom'))).toBe('boom')
  })

  it('returns the message of an ApiError', () => {
    expect(getErrorMessage(new ApiError(500, 'Server error'))).toBe('Server error')
  })

  it('returns the fallback for non-Error values', () => {
    expect(getErrorMessage('oops')).toBe('An unexpected error occurred')
  })

  it('honors a custom fallback', () => {
    expect(getErrorMessage(null, 'An unknown error occurred')).toBe('An unknown error occurred')
  })
})
