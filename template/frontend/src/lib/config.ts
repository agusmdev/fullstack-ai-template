/**
 * Application configuration with environment variable validation
 */

import { z } from 'zod'

/**
 * Environment variable schema
 * Validates all required environment variables at startup
 */
const envSchema = z.object({
  VITE_API_BASE_URL: z.string().url().default('http://localhost:9095'),
})

/**
 * Parse and validate environment variables
 * Will throw an error if validation fails
 */
const env = envSchema.parse({
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
})

/**
 * Validated and typed application configuration
 */
export const config = {
  /**
   * API base URL
   * Can be overridden with VITE_API_BASE_URL environment variable
   * @default http://localhost:9095
   */
  apiBaseUrl: env.VITE_API_BASE_URL,
} as const
