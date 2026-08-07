import { z } from 'zod'

/** Max name length mirrors the backend (`View.name` String(255)). */
export const VIEW_NAME_MAX = 255

/**
 * Save-view form schema.
 *
 * - `name` is required: non-empty after trimming whitespace (VAL-VIEWS-002)
 *   and within length bounds.
 */
export const saveViewFormSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, 'Name is required')
    .max(VIEW_NAME_MAX, `Name must be at most ${VIEW_NAME_MAX} characters`),
})

export type SaveViewFormValues = z.infer<typeof saveViewFormSchema>

/** Default save-view form values. */
export function defaultSaveViewFormValues(): SaveViewFormValues {
  return { name: '' }
}
