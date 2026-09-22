/**
 * Centralized error handling utilities for consistent error management
 * Provides standardized error handling across API adapters and components
 */

export interface ApiError {
  message: string
  status?: number
  code?: string
  details?: string
}

/**
 * Parse API error response into standardized format
 */
export function parseApiError(response: Response, errorData?: any): ApiError {
  const status = response.status
  let message = 'An error occurred'
  let details: string | undefined

  // Extract error message from various possible response formats
  if (errorData) {
    message = errorData.detail || errorData.error || errorData.message || message
    details = errorData.detail
  }

  // Provide user-friendly messages for common status codes
  switch (status) {
    case 400:
      message = errorData?.detail || 'Invalid request. Please check your input.'
      break
    case 401:
      message = 'Authentication required. Please log in.'
      break
    case 403:
      message = errorData?.detail || 'You do not have permission to perform this action.'
      break
    case 404:
      message = errorData?.detail || 'The requested resource was not found.'
      break
    case 429:
      message = 'Too many requests. Please try again later.'
      break
    case 500:
      message = 'Server error. Please try again later.'
      break
    case 503:
      message = 'Service unavailable. Please try again later.'
      break
  }

  return {
    message,
    status,
    details,
  }
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
