/**
 * Centralized error handling utilities for consistent error management
 * Provides standardized error handling across API adapters and components
 *
 * The backend returns errors in several shapes (see backend/common/exception_handlers.py):
 *   a) {error: {code, message, details}}   - uniform envelope from the DRF exception handler
 *   b) {error: "text", details?}           - hand-written view responses (booking create, property 404)
 *   c) {detail: "text"}                    - login 401, logout
 *   d) {success: false, message} or raw serializer errors {field: ["text"]} - OTP, register, profile
 * parseApiError reads all of them and always returns a plain string message.
 */

export interface ApiError {
  message: string
  status?: number
  code?: string
  details?: string
  fieldErrors?: Record<string, string[]>
}

/** Per-status fallback messages for an adapter (e.g. 403 on partner endpoints), used when the server gives no specific one. */
export type StatusMessages = Partial<Record<number, string>>

const STATUS_MESSAGES: Record<number, string> = {
  400: 'Invalid request. Please check your input.',
  401: 'Authentication required. Please log in.',
  403: 'You do not have permission to perform this action.',
  404: 'The requested resource was not found.',
  429: 'Too many requests. Please wait a moment and try again.',
  500: 'Server error. Please try again later.',
  503: 'Service temporarily unavailable. Please try again later.',
}

const CSRF_MESSAGE = 'Your session has expired. Please refresh the page and try again.'

// DRF defaults that say nothing useful to a user; the status message is shown instead
const GENERIC_SERVER_MESSAGES = new Set([
  'Authentication credentials were not provided.',
  'You do not have permission to perform this action.',
  'Not found.',
])

function isGenericServerMessage(message: string): boolean {
  // get_object_or_404 text, e.g. "No Favorite matches the given query."
  return GENERIC_SERVER_MESSAGES.has(message) || /^No \w+ matches the given query\.$/.test(message)
}

// Keys that are envelope metadata, not form fields
const NON_FIELD_KEYS = new Set(['detail', 'code', 'error', 'message', 'success', 'details', 'status_code'])

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function toMessages(value: unknown): string[] {
  if (typeof value === 'string') return [value]
  if (Array.isArray(value)) return value.flatMap(toMessages)
  if (isRecord(value)) return Object.values(value).flatMap(toMessages)
  return []
}

/** Field errors ({field: ["msg"]}) from a serializer errors dict, ignoring envelope keys. */
function extractFieldErrors(data: unknown): Record<string, string[]> | undefined {
  if (!isRecord(data)) return undefined
  const fieldErrors: Record<string, string[]> = {}
  for (const [key, value] of Object.entries(data)) {
    if (NON_FIELD_KEYS.has(key)) continue
    const messages = toMessages(value)
    if (messages.length > 0) fieldErrors[key] = messages
  }
  return Object.keys(fieldErrors).length > 0 ? fieldErrors : undefined
}

function humanizeField(field: string): string {
  const words = field.replace(/_/g, ' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}

function formatFieldErrors(fieldErrors: Record<string, string[]>): string {
  return Object.entries(fieldErrors)
    .map(([field, messages]) =>
      field === 'non_field_errors' ? messages.join(' ') : `${humanizeField(field)}: ${messages.join(' ')}`
    )
    .join(' ')
}

/** Pull the server's message, code and field errors out of any of the backend error shapes. */
function extractServerError(errorData: unknown): { message?: string; code?: string; fieldErrors?: Record<string, string[]> } {
  if (typeof errorData === 'string') {
    return { message: errorData || undefined }
  }
  if (!isRecord(errorData)) return {}

  // a) uniform envelope
  if (isRecord(errorData.error)) {
    const envelope = errorData.error
    const fieldErrors = extractFieldErrors(envelope.details)
    // For serializer errors the envelope message is a Python repr of the dict, so field errors win
    const message = fieldErrors
      ? formatFieldErrors(fieldErrors)
      : typeof envelope.message === 'string' ? envelope.message : undefined
    return {
      message,
      code: typeof envelope.code === 'string' ? envelope.code : undefined,
      fieldErrors,
    }
  }

  // b) flat {error: "text", details}
  if (typeof errorData.error === 'string') {
    const fieldErrors = extractFieldErrors(errorData.details)
    const message = fieldErrors ? `${errorData.error.replace(/\.?$/, '.')} ${formatFieldErrors(fieldErrors)}` : errorData.error
    return { message, fieldErrors }
  }

  // c) {detail}
  if (typeof errorData.detail === 'string') {
    return { message: errorData.detail }
  }

  // d) {success: false, message} or raw serializer errors
  if (typeof errorData.message === 'string') {
    return { message: errorData.message }
  }
  const fieldErrors = extractFieldErrors(errorData)
  if (fieldErrors) {
    return { message: formatFieldErrors(fieldErrors), fieldErrors }
  }
  return {}
}

function statusMessage(status: number): string {
  if (STATUS_MESSAGES[status]) return STATUS_MESSAGES[status]
  if (status >= 500) return STATUS_MESSAGES[500]
  return 'An error occurred'
}

/**
 * Parse API error response into standardized format
 */
export function parseApiError(response: Response, errorData?: unknown, overrides: StatusMessages = {}): ApiError {
  const status = response.status
  const server = extractServerError(errorData)
  // Adapter overrides replace the generic status text, never a specific server message
  const fallback = overrides[status] ?? statusMessage(status)
  let message: string

  if (status === 429) {
    const retryAfter = Number(response.headers?.get('Retry-After'))
    message = retryAfter > 0
      ? `Too many requests. Please try again in ${retryAfter} seconds.`
      : fallback
  } else if (status >= 500) {
    // Server-side text (exception names, provider errors) is not meant for users
    message = fallback
  } else if (status === 403 && server.message?.startsWith('CSRF Failed')) {
    message = CSRF_MESSAGE
  } else if (server.message && !isGenericServerMessage(server.message)) {
    message = server.message
  } else {
    message = fallback
  }

  return {
    message,
    status,
    code: server.code,
    details: server.message,
    fieldErrors: server.fieldErrors,
  }
}

/**
 * Read the body of a failed response and parse it. Every adapter uses this for non-2xx responses.
 */
export async function readApiError(response: Response, overrides: StatusMessages = {}): Promise<ApiError> {
  // An HTML error page or empty body is not JSON; parseApiError then falls back to the status message
  const errorData: unknown = await response.json().catch(() => undefined)
  return parseApiError(response, errorData, overrides)
}

/**
 * Handle network errors consistently
 */
export function handleNetworkError(error: unknown): ApiError {
  if (error instanceof Error) {
    // Check for specific network error types
    if (error.message.includes('fetch')) {
      return {
        message: 'Network error. Please check your connection.',
        code: 'NETWORK_ERROR',
      }
    }
    if (error.message.includes('timeout')) {
      return {
        message: 'Request timeout. Please try again.',
        code: 'TIMEOUT_ERROR',
      }
    }
    return {
      message: error.message,
      code: 'UNKNOWN_ERROR',
    }
  }

  return {
    message: 'An unexpected error occurred',
    code: 'UNKNOWN_ERROR',
  }
}

/**
 * Get user-friendly error message for display
 */
export function getUserErrorMessage(error: ApiError | Error | string): string {
  if (typeof error === 'string') {
    return error
  }

  if (error instanceof Error) {
    return error.message
  }

  if ('message' in error) {
    return error.message
  }

  return 'An unexpected error occurred'
}

/**
 * Check if error is authentication-related
 */
export function isAuthError(error: ApiError | Error): boolean {
  const status = 'status' in error ? error.status : undefined
  return status === 401 || status === 403
}

/**
 * Check if error is network-related
 */
export function isNetworkError(error: ApiError | Error): boolean {
  if ('code' in error) {
    return error.code === 'NETWORK_ERROR' || error.code === 'TIMEOUT_ERROR'
  }
  return false
}

/**
 * Check if error is server-related (5xx)
 */
export function isServerError(error: ApiError | Error): boolean {
  const status = 'status' in error ? error.status : undefined
  return status !== undefined && status >= 500 && status < 600
}
