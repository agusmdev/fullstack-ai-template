/**
 * Structured logging utility for the frontend.
 *
 * Provides consistent, structured log output with log levels,
 * context binding, and sensitive data redaction.
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

interface LogContext {
  [key: string]: unknown
}

const LOG_ORDER: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
}

const SENSITIVE_KEYS = new Set([
  'password',
  'token',
  'secret',
  'apiKey',
  'api_key',
  'authorization',
  'auth',
  'credential',
  'accessToken',
  'refreshToken',
  'bearer',
  'cookie',
  'sessionId',
])

function redactSensitive(context: LogContext): LogContext {
  const redacted: LogContext = {}
  for (const [key, value] of Object.entries(context)) {
    if (SENSITIVE_KEYS.has(key.toLowerCase())) {
      redacted[key] = '[REDACTED]'
    } else {
      redacted[key] = value
    }
  }
  return redacted
}

function shouldLog(level: LogLevel): boolean {
  const minLevel: LogLevel = (import.meta.env.VITE_LOG_LEVEL as LogLevel) ?? 'info'
  return LOG_ORDER[level] >= LOG_ORDER[minLevel]
}

function formatMessage(level: LogLevel, message: string, context?: LogContext): void {
  if (!shouldLog(level)) return

  const timestamp = new Date().toISOString()
  const safeContext = context ? redactSensitive(context) : undefined

  const logEntry = {
    timestamp,
    level,
    message,
    ...safeContext,
  }

  switch (level) {
    case 'debug':
      console.debug(logEntry)
      break
    case 'info':
      console.info(logEntry)
      break
    case 'warn':
      console.warn(logEntry)
      break
    case 'error':
      console.error(logEntry)
      break
  }
}

export const logger = {
  debug(message: string, context?: LogContext): void {
    formatMessage('debug', message, context)
  },
  info(message: string, context?: LogContext): void {
    formatMessage('info', message, context)
  },
  warn(message: string, context?: LogContext): void {
    formatMessage('warn', message, context)
  },
  error(message: string, context?: LogContext): void {
    formatMessage('error', message, context)
  },
}
