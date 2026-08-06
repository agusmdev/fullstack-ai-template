import { z } from 'zod'
import { PRIORITY_NONE } from '@/types/issue'

/**
 * Max title length mirrors the backend (`Issue.title` String(512), schema
 * max_length=512). The input enforces it client-side via maxLength so a paste
 * of an over-long string is clamped, never silently 500'd (VAL-ISSUES-004).
 */
export const ISSUE_TITLE_MAX = 512

/**
 * Create-issue form schema.
 *
 * - `title` is required: must be non-empty after trimming whitespace
 *   (VAL-ISSUES-002, VAL-ISSUES-003) and within length bounds (VAL-ISSUES-004).
 * - `description` is optional and supports multiline text (VAL-ISSUES-007).
 *
 * Status / priority / assignee / labels are validated by the backend (they are
 * always well-formed choices from pickers), so they are not part of the zod
 * form model here — the dialog manages them as controlled picker state and
 * merges them into the create payload on submit.
 */
export const createIssueFormSchema = z.object({
  title: z
    .string()
    .trim()
    .min(1, 'Title is required')
    .max(ISSUE_TITLE_MAX, `Title must be at most ${ISSUE_TITLE_MAX} characters`),
  description: z.string().optional(),
})

export type CreateIssueFormValues = z.infer<typeof createIssueFormSchema>

/**
 * The default create-issue form values.
 *
 * A title-only create applies the documented defaults: priority = No priority,
 * empty description; the status defaults to the team's first workflow state and
 * assignee to Unassigned (handled by the dialog from props) (VAL-ISSUES-005).
 */
export function defaultCreateIssueFormValues(): CreateIssueFormValues {
  return {
    title: '',
    description: '',
  }
}

/** Re-exported so callers can reference the canonical "no priority" default. */
export { PRIORITY_NONE }
