import { z } from 'zod'
import { DEFAULT_PROJECT_STATUS, PROJECT_STATUSES } from '@/types/project'

/** Max name length mirrors the backend (`Project.name` String(255)). */
export const PROJECT_NAME_MAX = 255

const validStatusValues = PROJECT_STATUSES.map((s) => s.value) as readonly string[]

/**
 * Create-project form schema.
 *
 * - `name` is required: non-empty after trimming whitespace (VAL-PROJECTS-001)
 *   and within length bounds.
 * - `status` defaults to a non-terminal value (planned) (VAL-PROJECTS-002).
 * - `target_date` is optional and must be a valid ISO date if provided
 *   (VAL-PROJECTS-004).
 *
 * `lead_id` is a controlled picker value (always a well-formed UUID or null),
 * so it is not part of the zod model.
 */
export const createProjectFormSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, 'Name is required')
    .max(PROJECT_NAME_MAX, `Name must be at most ${PROJECT_NAME_MAX} characters`),
  status: z.enum(validStatusValues as [string, ...string[]]).default(
    DEFAULT_PROJECT_STATUS,
  ),
  target_date: z
    .string()
    .optional()
    .refine(
      (v) => !v || !Number.isNaN(Date.parse(v)),
      'Enter a valid date',
    ),
})

export type CreateProjectFormValues = z.infer<typeof createProjectFormSchema>

/** Default create-project form values (status defaults to planned). */
export function defaultCreateProjectFormValues(): CreateProjectFormValues {
  return {
    name: '',
    status: DEFAULT_PROJECT_STATUS,
    target_date: '',
  }
}
