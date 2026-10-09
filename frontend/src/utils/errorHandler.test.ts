import { describe, it, expect } from 'vitest'
import {
  parseApiError,
  readApiError,
  handleNetworkError,
  getUserErrorMessage,
  isAuthError,
  isNetworkError,
  isServerError,
  type ApiError,
} from './errorHandler'

describe('errorHandler', () => {
  describe('parseApiError', () => {
    it('parses error response with detail field', () => {
      const response = new Response('Not found', { status: 404 })
      const errorData = { detail: 'Resource not found' }
      
      const result = parseApiError(response, errorData)
      
      expect(result.message).toBe('Resource not found')
      expect(result.status).toBe(404)
      expect(result.details).toBe('Resource not found')
    })

    it('parses error response with error field', () => {
      const response = new Response('Bad request', { status: 400 })
      const errorData = { error: 'Invalid input' }
      
      const result = parseApiError(response, errorData)
      
      expect(result.message).toBe('Invalid input')
      expect(result.status).toBe(400)
    })

    it('provides default message for 401 status', () => {
      const response = new Response('Unauthorized', { status: 401 })
      
      const result = parseApiError(response)
      
      expect(result.message).toBe('Authentication required. Please log in.')
      expect(result.status).toBe(401)
    })

    it('provides default message for 403 status', () => {
      const response = new Response('Forbidden', { status: 403 })
      
      const result = parseApiError(response)
      
      expect(result.message).toBe('You do not have permission to perform this action.')
      expect(result.status).toBe(403)
    })

    it('provides default message for 404 status', () => {
      const response = new Response('Not found', { status: 404 })
      
      const result = parseApiError(response)
      
      expect(result.message).toBe('The requested resource was not found.')
      expect(result.status).toBe(404)
    })

    it('provides default message for 500 status', () => {
      const response = new Response('Server error', { status: 500 })
      
      const result = parseApiError(response)
      
      expect(result.message).toBe('Server error. Please try again later.')
      expect(result.status).toBe(500)
    })

    it('handles unknown status codes', () => {
      const response = new Response('Unknown error', { status: 418 })
      
      const result = parseApiError(response)
      
      expect(result.message).toBe('An error occurred')
      expect(result.status).toBe(418)
    })
  })

  describe('backend error shapes', () => {
    const res = (status: number, headers: Record<string, string> = {}) =>
      new Response(null, { status, headers })

    it('reads the uniform envelope message', () => {
      const body = { error: { code: 'permission_denied', message: 'Only the booking owner can review it.', details: { detail: 'Only the booking owner can review it.' } } }

      expect(parseApiError(res(403), body).message).toBe('Only the booking owner can review it.')
      expect(parseApiError(res(403), body).code).toBe('permission_denied')
    })

    it('builds the message from envelope field errors instead of the Python repr', () => {
      const body = {
        error: {
          code: 'error',
          message: "{'booking': [ErrorDetail(string='This field is required.', code='required')]}",
          details: { booking: ['This field is required.'], overall_rating: ['Ensure this value is less than or equal to 5.'] },
        },
      }

      const result = parseApiError(res(400), body)

      expect(result.message).toBe('Booking: This field is required. Overall rating: Ensure this value is less than or equal to 5.')
      expect(result.fieldErrors).toEqual({ booking: ['This field is required.'], overall_rating: ['Ensure this value is less than or equal to 5.'] })
    })

    it('shows non_field_errors without a field prefix', () => {
      const body = { error: { code: 'error', message: 'x', details: { non_field_errors: ['You already reviewed this booking.'] } } }

      expect(parseApiError(res(400), body).message).toBe('You already reviewed this booking.')
    })

    it('reads a flat error string with field details', () => {
      const body = { error: 'Booking validation failed', details: { check_in: ['Check-in date cannot be in the past.'] } }

      expect(parseApiError(res(400), body).message).toBe('Booking validation failed. Check in: Check-in date cannot be in the past.')
    })

    it('reads a flat error string', () => {
      expect(parseApiError(res(404), { error: 'Property not found' }).message).toBe('Property not found')
    })

    it('reads {success: false, message}', () => {
      expect(parseApiError(res(400), { success: false, message: 'Invalid or expired OTP code' }).message).toBe('Invalid or expired OTP code')
    })

    it('reads raw serializer errors', () => {
      expect(parseApiError(res(400), { phone_number: ['Enter a valid phone number.'] }).message).toBe('Phone number: Enter a valid phone number.')
    })

    it('never returns an object as the message', () => {
      const result = parseApiError(res(400), { error: { code: 'error' } })

      expect(typeof result.message).toBe('string')
      expect(result.message).toBe('Invalid request. Please check your input.')
    })
  })

  describe('status messages', () => {
    const res = (status: number, headers: Record<string, string> = {}) =>
      new Response(null, { status, headers })

    it('400 without a server message', () => {
      expect(parseApiError(res(400), {}).message).toBe('Invalid request. Please check your input.')
    })

    it('401 keeps a specific message such as failed login', () => {
      const body = { detail: 'Invalid credentials. If you have made several failed attempts, please try again later.' }

      expect(parseApiError(res(401), body).message).toBe(body.detail)
    })

    it('401 replaces the DRF default with a login prompt', () => {
      const body = { error: { code: 'not_authenticated', message: 'Authentication credentials were not provided.', details: {} } }

      expect(parseApiError(res(401), body).message).toBe('Authentication required. Please log in.')
    })

    it('403 CSRF failure asks to refresh', () => {
      const body = { error: { code: 'error', message: 'CSRF Failed: CSRF token missing.', details: {} } }

      expect(parseApiError(res(403), body, { 403: 'Hotel-owner role required' }).message).toBe(
        'Your session has expired. Please refresh the page and try again.'
      )
    })

    it('403 replaces the DRF default', () => {
      const body = { error: { code: 'permission_denied', message: 'You do not have permission to perform this action.', details: {} } }

      expect(parseApiError(res(403), body).message).toBe('You do not have permission to perform this action.')
      expect(parseApiError(res(403), body, { 403: 'Hotel-owner role required' }).message).toBe('Hotel-owner role required')
    })

    it('404 replaces get_object_or_404 text', () => {
      expect(parseApiError(res(404), { detail: 'No Booking matches the given query.' }).message).toBe(
        'The requested resource was not found.'
      )
    })

    it('429 uses Retry-After when present', () => {
      const body = { error: { code: 'throttled', message: 'Request was throttled. Expected available in 42 seconds.', details: {} } }

      expect(parseApiError(res(429), body).message).toBe('Too many requests. Please wait a moment and try again.')
      expect(parseApiError(res(429, { 'Retry-After': '42' }), body).message).toBe('Too many requests. Please try again in 42 seconds.')
    })

    it('503 hides provider details', () => {
      const body = { error: { code: 'external_service_error', message: 'SMS provider is not configured', details: null } }

      expect(parseApiError(res(503), body).message).toBe('Service temporarily unavailable. Please try again later.')
    })
  })

  describe('readApiError', () => {
    it('parses a JSON body', async () => {
      const response = new Response(JSON.stringify({ error: { code: 'x', message: 'Booking cannot be cancelled.', details: null } }), { status: 400 })

      expect((await readApiError(response)).message).toBe('Booking cannot be cancelled.')
    })

    it('falls back to the status message for an HTML body', async () => {
      const response = new Response('<html>Bad Gateway</html>', { status: 502 })

      expect((await readApiError(response)).message).toBe('Server error. Please try again later.')
    })
  })

  describe('handleNetworkError', () => {
    it('handles fetch errors', () => {
      const error = new Error('Failed to fetch')
      
      const result = handleNetworkError(error)
      
      expect(result.message).toBe('Network error. Please check your connection.')
      expect(result.code).toBe('NETWORK_ERROR')
    })

    it('handles timeout errors', () => {
      const error = new Error('Request timeout')
      
      const result = handleNetworkError(error)
      
      expect(result.message).toBe('Request timeout. Please try again.')
      expect(result.code).toBe('TIMEOUT_ERROR')
    })

    it('handles generic errors', () => {
      const error = new Error('Some error')
      
      const result = handleNetworkError(error)
      
      expect(result.message).toBe('Some error')
      expect(result.code).toBe('UNKNOWN_ERROR')
    })

    it('handles non-error objects', () => {
      const result = handleNetworkError('string error')
      
      expect(result.message).toBe('An unexpected error occurred')
      expect(result.code).toBe('UNKNOWN_ERROR')
    })
  })

  describe('getUserErrorMessage', () => {
    it('returns string error as-is', () => {
      const result = getUserErrorMessage('String error')
      
      expect(result).toBe('String error')
    })

    it('returns Error message', () => {
      const error = new Error('Error message')
      
      const result = getUserErrorMessage(error)
      
      expect(result).toBe('Error message')
    })

    it('returns ApiError message', () => {
      const error: ApiError = { message: 'API error message' }
      
      const result = getUserErrorMessage(error)
      
      expect(result).toBe('API error message')
    })

    it('returns default message for unknown types', () => {
      const result = getUserErrorMessage({} as never)
      
      expect(result).toBe('An unexpected error occurred')
    })
  })

  describe('isAuthError', () => {
    it('returns true for 401 status', () => {
      const error: ApiError = { message: 'Auth error', status: 401 }
      
      expect(isAuthError(error)).toBe(true)
    })

    it('returns true for 403 status', () => {
      const error: ApiError = { message: 'Auth error', status: 403 }
      
      expect(isAuthError(error)).toBe(true)
    })

    it('returns false for other statuses', () => {
      const error: ApiError = { message: 'Other error', status: 404 }
      
      expect(isAuthError(error)).toBe(false)
    })

    it('returns false for Error objects', () => {
      const error = new Error('Some error')
      
      expect(isAuthError(error)).toBe(false)
    })
  })

  describe('isNetworkError', () => {
    it('returns true for NETWORK_ERROR code', () => {
      const error: ApiError = { message: 'Network error', code: 'NETWORK_ERROR' }
      
      expect(isNetworkError(error)).toBe(true)
    })

    it('returns true for TIMEOUT_ERROR code', () => {
      const error: ApiError = { message: 'Timeout error', code: 'TIMEOUT_ERROR' }
      
      expect(isNetworkError(error)).toBe(true)
    })

    it('returns false for other codes', () => {
      const error: ApiError = { message: 'Other error', code: 'OTHER_ERROR' }
      
      expect(isNetworkError(error)).toBe(false)
    })

    it('returns false for Error objects', () => {
      const error = new Error('Some error')
      
      expect(isNetworkError(error)).toBe(false)
    })
  })

  describe('isServerError', () => {
    it('returns true for 500 status', () => {
      const error: ApiError = { message: 'Server error', status: 500 }
      
      expect(isServerError(error)).toBe(true)
    })

    it('returns true for 503 status', () => {
      const error: ApiError = { message: 'Service unavailable', status: 503 }
      
      expect(isServerError(error)).toBe(true)
    })

    it('returns false for 4xx statuses', () => {
      const error: ApiError = { message: 'Client error', status: 404 }
      
      expect(isServerError(error)).toBe(false)
    })

    it('returns false for Error objects', () => {
      const error = new Error('Some error')
      
      expect(isServerError(error)).toBe(false)
    })
  })
})
