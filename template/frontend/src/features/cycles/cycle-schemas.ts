import { z } from 'zod'

/** Max name length mirrors the backend (`Cycle.name` String(255)). */
export const CYCLE_NAME_MAX = 255

/**
 * Create-cycle form schema.
 *
 * - `name` is required: non-empty after trimming whitespace (VAL-CYCLES-001).
 * - `starts_at` and `ends_at` are required dates (VAL-CYCLES-001).
 * - `ends_at` must be strictly after `starts_at` (VAL-CYCLES-002).
 *
 * Dates are managed as native ``<input type="date">`` values (YYYY-MM-DD).
 */
export const createCycleFormSchema = z
  .object({
    name: z
      .string()
      .trim()
      .min(1, 'Name is required')
      .max(CYCLE_NAME_MAX, `Name must be at most ${CYCLE_NAME_MAX} characters`),
    starts_at: z
      .string()
      .min(1, 'Start date is required')
      .refine((v) => !Number.isNaN(Date.parse(v)), 'Enter a valid start date'),
    ends_at: z
      .string()
      .min(1, 'End date is required')
      .refine((v) => !Number.isNaN(Date.parse(v)), 'Enter a valid end date'),
  })
  .refine((data) => new Date(data.ends_at) > new Date(data.starts_at), {
    message: 'End date must be after start date',
    path: ['ends_at'],
  })

export type CreateCycleFormValues = z.infer<typeof createCycleFormSchema>

/** Default create-cycle form values (all empty — name+start+end required). */
export function defaultCreateCycleFormValues(): CreateCycleFormValues {
  return {
    name: '',
    starts_at: '',
    ends_at: '',
  }
}
