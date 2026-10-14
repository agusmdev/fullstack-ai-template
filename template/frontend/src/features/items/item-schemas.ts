import { z } from 'zod'

export const itemSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255, 'Name must be less than 255 characters'),
  description: z.string().max(5000, 'Description must be less than 5000 characters').optional(),
})

export type ItemFormData = z.infer<typeof itemSchema>

/**
 * Maps form values to the mutation payload shape expected by item API hooks.
 * An empty description is sent as `null`, not left out: the update endpoint
 * keeps fields that are missing from the body, so `null` is how a user clears it.
 */
export function itemFormToPayload(data: ItemFormData) {
  return { name: data.name, description: data.description || null }
}
