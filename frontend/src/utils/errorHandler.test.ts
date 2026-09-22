import { describe, it, expect } from 'vitest'
import {
  parseApiError,
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
      
      expect(result.message).toBe('Invalid request. Please check your input.')
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
      const result = getUserErrorMessage({} as any)
      
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
