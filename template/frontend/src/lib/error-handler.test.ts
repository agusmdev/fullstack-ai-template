import { describe, it, expect, vi, beforeEach } from 'vitest'
import { handleApiError } from './error-handler'
import { ApiError } from './api-client'

vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
  },
}))

import { toast } from 'sonner'

describe('handleApiError', () => {
  beforeEach(() => {
    vi.mocked(toast.error).mockClear()
  })

  it('shows one toast per field when ApiError has field errors', () => {
    const err = new ApiError(422, 'Validation failed', 'validation_error', {
      email: ['Invalid email'],
      password: ['Too short', 'Must contain a number'],
    })

    handleApiError(err, 'Save failed')

    expect(toast.error).toHaveBeenCalledTimes(2)
    expect(toast.error).toHaveBeenCalledWith('email: Invalid email')
    expect(toast.error).toHaveBeenCalledWith('password: Too short, Must contain a number')
  })

  it('shows fallback message with error description when ApiError has no fields', () => {
    const err = new ApiError(500, 'Internal server error')

    handleApiError(err, 'Request failed')

    expect(toast.error).toHaveBeenCalledTimes(1)
    expect(toast.error).toHaveBeenCalledWith('Request failed', {
      description: 'Internal server error',
    })
  })

  it('shows fallback message with Error.message for plain Error', () => {
    const err = new Error('Network timeout')

    handleApiError(err, 'Connection failed')

    expect(toast.error).toHaveBeenCalledTimes(1)
    expect(toast.error).toHaveBeenCalledWith('Connection failed', {
      description: 'Network timeout',
    })
  })

  it('shows generic description for non-Error thrown values', () => {
    handleApiError('something went wrong', 'Unexpected failure')

    expect(toast.error).toHaveBeenCalledTimes(1)
    expect(toast.error).toHaveBeenCalledWith('Unexpected failure', {
      description: 'An unexpected error occurred',
    })
  })
})
