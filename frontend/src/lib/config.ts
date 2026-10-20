import { z } from 'zod'

const envSchema = z.object({
  VITE_API_BASE_URL: z.string().url().default('http://localhost:9095'),
})

export function getConfig() {
  const env = envSchema.parse({ VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL })
  return {
    /** @default http://localhost:9095 */
    apiBaseUrl: env.VITE_API_BASE_URL,
  }
}
