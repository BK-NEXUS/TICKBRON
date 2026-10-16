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

  describe('getCurrentUser only if there is a session', () => {
    it('does not ask /auth/me/ when the session is anonymous', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ csrf_token: 't', authenticated: false }) })

      const response = await adapter.getCurrentUser({ onlyIfSession: true })

      expect(response.success).toBe(false)
      expect(mockFetch).toHaveBeenCalledTimes(1)
      expect(mockFetch).toHaveBeenCalledWith('http://test-api/api/v1/auth/csrf/', expect.objectContaining({ credentials: 'include' }))
      expect(mockFetch).not.toHaveBeenCalledWith('http://test-api/api/v1/auth/me/', expect.anything())
    })

    it('asks /auth/me/ when the session is logged in', async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: true, json: async () => ({ csrf_token: 't', authenticated: true }) })
        .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1, email: 'test@example.com' }) })

      const response = await adapter.getCurrentUser({ onlyIfSession: true })

      expect(response.success).toBe(true)
      expect(response.user).toEqual(expect.objectContaining({ id: 1 }))
      expect(mockFetch).toHaveBeenLastCalledWith('http://test-api/api/v1/auth/me/', expect.objectContaining({ method: 'GET' }))
    })

    it('asks /auth/me/ when the session check fails', async () => {
      mockFetch
        .mockRejectedValueOnce(new Error('network'))
        .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1, email: 'test@example.com' }) })

      const response = await adapter.getCurrentUser({ onlyIfSession: true })

      expect(response.success).toBe(true)
    })
  })

})

describe('authAdapter singleton', () => {
  it('exports a singleton instance', () => {
    expect(authAdapter).toBeInstanceOf(AuthAdapter)
  })
})

describe('AuthAdapter password calls', () => {
  let adapter: AuthAdapter
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    adapter = new AuthAdapter('http://test-api')
    mockFetch = vi.fn()
    global.fetch = mockFetch
  })

  const sentBody = () => JSON.parse(mockFetch.mock.calls[0][1].body)

  it('requests a reset link for an address', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ detail: 'If this address is registered...' }) })

    const response = await adapter.requestPasswordReset('guest@example.com')

    expect(mockFetch).toHaveBeenCalledWith(
      'http://test-api/api/v1/auth/password-reset/request/',
      expect.objectContaining({ method: 'POST', credentials: 'include' })
    )
    expect(sentBody()).toEqual({ email: 'guest@example.com' })
    expect(response).toEqual({ success: true, error: undefined, code: undefined })
  })

  it('confirms a reset with the link values', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ detail: 'ok' }) })
    const data = { uid: 'MQ', token: 'abc', password: 'Fresh9Grape#Tower42', password_confirm: 'Fresh9Grape#Tower42' }

    const response = await adapter.confirmPasswordReset(data)

    expect(mockFetch.mock.calls[0][0]).toBe('http://test-api/api/v1/auth/password-reset/confirm/')
    expect(sentBody()).toEqual(data)
    expect(response.success).toBe(true)
  })

  it('hands the machine-readable code of a rejected link to the caller', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ error: 'This link is invalid or has expired.', code: 'invalid_reset_link' }),
    })

    const response = await adapter.confirmPasswordReset({ uid: 'x', token: 'y', password: 'a', password_confirm: 'a' })

    expect(response).toEqual({ success: false, error: 'This link is invalid or has expired.', code: 'invalid_reset_link' })
  })

  it('changes the password and returns the server message when it is refused', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ current_password: ['The current password is incorrect.'] }),
    })

    const response = await adapter.changePassword({ current_password: 'x', password: 'y', password_confirm: 'y' })

    expect(mockFetch.mock.calls[0][0]).toBe('http://test-api/api/v1/auth/password/change/')
    expect(response.success).toBe(false)
    expect(response.error).toContain('The current password is incorrect.')
  })
})
