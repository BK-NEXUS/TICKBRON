import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { AuthProvider, useAuth } from './AuthContext'
import { authAdapter } from '../adapters/authAdapter'

// Mock the auth adapter
vi.mock('../adapters/authAdapter', () => ({
  authAdapter: {
    getCurrentUser: vi.fn().mockResolvedValue({ success: false }),
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  },
}))

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <AuthProvider>{children}</AuthProvider>
  )

  describe('initial state', () => {
    it('provides default auth state', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper })

      // Wait for initial auth check to complete
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })

      expect(result.current.user).toBeNull()
      expect(result.current.isLoading).toBe(false)
      expect(result.current.isAuthenticated).toBe(false)
    })
  })

  describe('getCurrentUser on mount', () => {
    it('checks authentication status on mount', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe',
        full_name: 'John Doe',
        is_active: true,
        date_joined: '2024-01-01T00:00:00Z',
        email_verified: true,
        two_factor_enabled: false,
      }

      vi.mocked(authAdapter.getCurrentUser).mockResolvedValueOnce({
        success: true,
        user: mockUser,
      })

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })

      expect(result.current.user).toEqual(mockUser)
      expect(result.current.isAuthenticated).toBe(true)
    })

    it('handles unauthenticated state', async () => {
      vi.mocked(authAdapter.getCurrentUser).mockResolvedValueOnce({
        success: false,
        error: 'Not authenticated',
      })

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })

      expect(result.current.user).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)
    })
  })

  describe('login', () => {
    it('logs in user successfully', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe',
        full_name: 'John Doe',
        is_active: true,
        date_joined: '2024-01-01T00:00:00Z',
        email_verified: true,
        two_factor_enabled: false,
      }

      vi.mocked(authAdapter.login).mockResolvedValue({
        success: true,
        user: mockUser,
      })

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })

      const response = await act(async () => {
        return await result.current.login('test@example.com', 'password')
      })

      expect(response.success).toBe(true)
      expect(result.current.user).toEqual(mockUser)
      expect(result.current.isAuthenticated).toBe(true)
    })

    it('handles login failure', async () => {
      vi.mocked(authAdapter.login).mockResolvedValue({
        success: false,
        error: 'Invalid credentials',
      })

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })

      const response = await act(async () => {
        return await result.current.login('test@example.com', 'wrongpassword')
      })

      expect(response.success).toBe(false)
      expect(response.error).toBe('Invalid credentials')
      expect(result.current.user).toBeNull()
    })
  })

  describe('register', () => {
    it('registers user successfully', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe',
        full_name: 'John Doe',
        is_active: true,
        date_joined: '2024-01-01T00:00:00Z',
        email_verified: false,
        two_factor_enabled: false,
      }

      vi.mocked(authAdapter.register).mockResolvedValue({
        success: true,
        user: mockUser,
      })

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })

      const response = await act(async () => {
        return await result.current.register({
          email: 'test@example.com',
          first_name: 'John',
          last_name: 'Doe',
          password: 'SecurePassword123!',
          password_confirm: 'SecurePassword123!',
        })
      })

      expect(response.success).toBe(true)
      expect(result.current.user).toEqual(mockUser)
      expect(result.current.isAuthenticated).toBe(true)
    })

    it('handles registration failure', async () => {
      vi.mocked(authAdapter.register).mockResolvedValue({
        success: false,
        error: 'Email already exists',
      })

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })

      const response = await act(async () => {
        return await result.current.register({
          email: 'test@example.com',
          first_name: 'John',
          last_name: 'Doe',
          password: 'SecurePassword123!',
          password_confirm: 'SecurePassword123!',
        })
      })

      expect(response.success).toBe(false)
      expect(response.error).toBe('Email already exists')
    })
  })

  describe('logout', () => {
    it('logs out user successfully', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe',
        full_name: 'John Doe',
        is_active: true,
        date_joined: '2024-01-01T00:00:00Z',
        email_verified: true,
        two_factor_enabled: false,
      }

      vi.mocked(authAdapter.getCurrentUser).mockResolvedValueOnce({
        success: true,
        user: mockUser,
      })
      vi.mocked(authAdapter.logout).mockResolvedValue({
        success: true,
      })

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })

      expect(result.current.isAuthenticated).toBe(true)

      const response = await act(async () => {
        return await result.current.logout()
      })

      expect(response.success).toBe(true)
      expect(result.current.user).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)
    })

    it('handles logout failure', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe',
        full_name: 'John Doe',
        is_active: true,
        date_joined: '2024-01-01T00:00:00Z',
        email_verified: true,
        two_factor_enabled: false,
      }

      vi.mocked(authAdapter.getCurrentUser).mockResolvedValueOnce({
        success: true,
        user: mockUser,
      })
      vi.mocked(authAdapter.logout).mockResolvedValue({
        success: false,
        error: 'Logout failed',
      })

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })

      const response = await act(async () => {
        return await result.current.logout()
      })

      expect(response.success).toBe(false)
      expect(result.current.user).toEqual(mockUser) // User should remain on failure
    })
  })

  describe('refreshUser', () => {
    it('refreshes user data', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe',
        full_name: 'John Doe',
        is_active: true,
        date_joined: '2024-01-01T00:00:00Z',
        email_verified: true,
        two_factor_enabled: false,
      }

      vi.mocked(authAdapter.getCurrentUser).mockResolvedValueOnce({
        success: true,
        user: mockUser,
      })

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })

      await act(async () => {
        await result.current.refreshUser()
      })

      expect(authAdapter.getCurrentUser).toHaveBeenCalled()
    })

    it('clears user on refresh failure', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe',
        full_name: 'John Doe',
        is_active: true,
        date_joined: '2024-01-01T00:00:00Z',
        email_verified: true,
        two_factor_enabled: false,
      }

      vi.mocked(authAdapter.getCurrentUser)
        .mockResolvedValueOnce({
          success: true,
          user: mockUser,
        })
        .mockResolvedValueOnce({
          success: false,
        })

      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })

      expect(result.current.isAuthenticated).toBe(true)

      await act(async () => {
        await result.current.refreshUser()
      })

      expect(result.current.user).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)
    })
  })

  describe('useAuth hook', () => {
    it('throws error when used outside AuthProvider', () => {
      // Suppress console.error for this test
      const consoleError = console.error
      console.error = vi.fn()

      expect(() => {
        renderHook(() => useAuth())
      }).toThrow('useAuth must be used within an AuthProvider')

      console.error = consoleError
    })
  })
})
