import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { AuthAdapter, authAdapter } from './authAdapter'

describe('AuthAdapter', () => {
  let adapter: AuthAdapter
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    adapter = new AuthAdapter('http://test-api')
    mockFetch = vi.fn()
    global.fetch = mockFetch
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('register', () => {
    it('sends registration request with correct data', async () => {
      const userData = {
        email: 'test@example.com',
        full_name: 'John Doe',
        phone_number: '+1234567890',
        password: 'SecurePassword123!',
        password_confirm: 'SecurePassword123!',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 1,
          email: userData.email,
          first_name: '',
          last_name: '',
          full_name: userData.full_name,
          is_active: true,
          date_joined: '2024-01-01T00:00:00Z',
          email_verified: false,
          two_factor_enabled: false,
        }),
      })

      const response = await adapter.register(userData)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/auth/register/',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(userData),
        })
      )
      expect(response.success).toBe(true)
      expect(response.user).toBeDefined()
    })

    it('handles registration errors', async () => {
      const userData = {
        email: 'test@example.com',
        full_name: 'John Doe',
        phone_number: '+1234567890',
        password: 'SecurePassword123!',
        password_confirm: 'SecurePassword123!',
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Email already exists' }),
      })

      const response = await adapter.register(userData)

      expect(response.success).toBe(false)
      expect(response.error).toBe('Email already exists')
    })

    it('handles network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const response = await adapter.register({
        email: 'test@example.com',
        full_name: 'John Doe',
        phone_number: '+1234567890',
        password: 'SecurePassword123!',
        password_confirm: 'SecurePassword123!',
      })

      expect(response.success).toBe(false)
      expect(response.error).toBe('Network error')
    })
  })

  describe('login', () => {
    it('sends login request with correct data', async () => {
      const loginData = {
        email: 'test@example.com',
        password: 'SecurePassword123!',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 1,
          email: loginData.email,
          first_name: 'John',
          last_name: 'Doe',
          full_name: 'John Doe',
          is_active: true,
          date_joined: '2024-01-01T00:00:00Z',
          email_verified: true,
          two_factor_enabled: false,
        }),
      })

      const response = await adapter.login(loginData)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/auth/login/',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify(loginData),
        })
      )
      expect(response.success).toBe(true)
      expect(response.user).toBeDefined()
    })

    it('handles login errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Invalid credentials' }),
      })

      const response = await adapter.login({
        email: 'test@example.com',
        password: 'wrongpassword',
      })

      expect(response.success).toBe(false)
      expect(response.error).toBe('Invalid credentials')
    })
  })

  describe('logout', () => {
    it('sends logout request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ detail: 'Successfully logged out.' }),
      })

      const response = await adapter.logout()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/auth/logout/',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
        })
      )
      expect(response.success).toBe(true)
    })
  })

  describe('refresh', () => {
    it('sends refresh request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 1,
          email: 'test@example.com',
          first_name: 'John',
          last_name: 'Doe',
          full_name: 'John Doe',
          is_active: true,
          date_joined: '2024-01-01T00:00:00Z',
          email_verified: true,
          two_factor_enabled: false,
        }),
      })

      const response = await adapter.refresh()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/auth/refresh/',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
        })
      )
      expect(response.success).toBe(true)
      expect(response.user).toBeDefined()
    })
  })

  describe('getCurrentUser', () => {
    it('sends get current user request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 1,
          email: 'test@example.com',
          first_name: 'John',
          last_name: 'Doe',
          full_name: 'John Doe',
          is_active: true,
          date_joined: '2024-01-01T00:00:00Z',
          email_verified: true,
          two_factor_enabled: false,
        }),
      })

      const response = await adapter.getCurrentUser()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/auth/me/',
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      )
      expect(response.success).toBe(true)
      expect(response.user).toBeDefined()
    })

    it('handles unauthenticated state', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Authentication required' }),
      })

      const response = await adapter.getCurrentUser()

      expect(response.success).toBe(false)
      expect(response.error).toBe('Authentication required')
    })
  })

  describe('requestOTP', () => {
    it('sends OTP request with correct data', async () => {
      const otpData = {
        phone_number: '+1234567890',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          otp_code: '123456',
        }),
      })

      const response = await adapter.requestOTP(otpData)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/auth/otp/request/',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(otpData),
        })
      )
      expect(response.success).toBe(true)
      expect(response.otp_code).toBe('123456')
    })

    it('handles OTP request errors', async () => {
      const otpData = {
        phone_number: 'invalid',
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Invalid phone number' }),
      })

      const response = await adapter.requestOTP(otpData)

      expect(response.success).toBe(false)
      expect(response.error).toBe('Invalid phone number')
    })

    it('returns a string message for a throttled request in the uniform envelope', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        headers: new Headers({ 'Retry-After': '30' }),
        json: async () => ({
          error: { code: 'throttled', message: 'Request was throttled. Expected available in 30 seconds.', details: {} },
        }),
      })

      const response = await adapter.requestOTP({ phone_number: '+998901234567' })

      expect(response.success).toBe(false)
      expect(response.error).toBe('Too many requests. Please try again in 30 seconds.')
    })

    it('returns a string message when the SMS provider is unavailable', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 503,
        json: async () => ({
          error: { code: 'external_service_error', message: 'SMS service unavailable', details: null },
        }),
      })

      const response = await adapter.requestOTP({ phone_number: '+998901234567' })

      expect(response.error).toBe('Service temporarily unavailable. Please try again later.')
    })

    it('handles network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const response = await adapter.requestOTP({
        phone_number: '+1234567890',
      })

      expect(response.success).toBe(false)
      expect(response.error).toBe('Network error')
    })
  })

  describe('verifyOTP', () => {
    it('sends OTP verification request with correct data', async () => {
      const otpData = {
        phone_number: '+1234567890',
        otp_code: '123456',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 1,
          email: 'test@example.com',
          first_name: 'John',
          last_name: 'Doe',
          full_name: 'John Doe',
          is_active: true,
          date_joined: '2024-01-01T00:00:00Z',
          email_verified: true,
          two_factor_enabled: false,
        }),
      })

      const response = await adapter.verifyOTP(otpData)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/auth/otp/verify/',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify(otpData),
        })
      )
      expect(response.success).toBe(true)
      expect(response.user).toBeDefined()
    })

    it('handles OTP verification errors', async () => {
      const otpData = {
        phone_number: '+1234567890',
        otp_code: '000000',
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Invalid code' }),
      })

      const response = await adapter.verifyOTP(otpData)

      expect(response.success).toBe(false)
      expect(response.error).toBe('Invalid code')
    })

    it('handles network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const response = await adapter.verifyOTP({
        phone_number: '+1234567890',
        otp_code: '123456',
      })

      expect(response.success).toBe(false)
      expect(response.error).toBe('Network error')
    })
  })
})

describe('authAdapter singleton', () => {
  it('exports a singleton instance', () => {
    expect(authAdapter).toBeInstanceOf(AuthAdapter)
  })
})
