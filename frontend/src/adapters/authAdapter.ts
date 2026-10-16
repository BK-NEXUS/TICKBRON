// Auth API adapter for session-based authentication
// Integrates with backend auth endpoints from Checkpoint 03-04

import { readApiError } from '../utils/errorHandler'
import { apiFetch, clearCsrfToken } from '../utils/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  phone_number?: string
  whatsapp?: string
  telegram?: string
  preferred_contact_method?: 'phone' | 'whatsapp' | 'telegram' | 'email'
  is_active: boolean
  date_joined: string
  last_login?: string
  email_verified: boolean
  two_factor_enabled: boolean
  is_staff?: boolean
  is_superuser?: boolean
  // Role name, e.g. 'hotel-owner'; null for regular users. Read-only on the backend
  role?: string | null
}

export interface RegisterRequest {
  email: string
  full_name: string
  password: string
  password_confirm: string
  first_name?: string
  last_name?: string
  whatsapp?: string
  telegram?: string
  preferred_contact_method?: 'phone' | 'whatsapp' | 'telegram' | 'email'
}

export interface UpdateProfileRequest {
  full_name?: string
  first_name?: string
  last_name?: string
  phone_number?: string
  whatsapp?: string
  telegram?: string
  preferred_contact_method?: 'phone' | 'whatsapp' | 'telegram' | 'email'
}

export interface LoginRequest {
  email: string
  password: string
}

export interface AuthResponse {
  success: boolean
  user?: User
  error?: string
  /** Machine-readable reason from the backend, e.g. 'otp_invalid' */
  code?: string
  detail?: string
}

export interface ResetPasswordRequest {
  uid: string
  token: string
  password: string
  password_confirm: string
}

export interface ChangePasswordRequest {
  current_password: string
  password: string
  password_confirm: string
}

/** The answer of a password call: only whether it worked, never the account. */
export interface PasswordActionResponse {
  success: boolean
  error?: string
  /** Machine-readable reason from the backend, e.g. 'invalid_reset_link' */
  code?: string
}

class AuthAdapter {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<AuthResponse> {
    const url = `${this.baseUrl}${endpoint}`
    
    const defaultOptions: RequestInit = {
      credentials: 'include', // Important for session-based auth with cookies
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    }

    try {
      const response = await apiFetch(url, defaultOptions)
      
      if (!response.ok) {
        const apiError = await readApiError(response)
        return {
          success: false,
          error: apiError.message,
          code: apiError.code,
        }
      }

      const data = await response.json()
      return {
        success: true,
        user: data,
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error occurred',
      }
    }
  }

  // Django rotates the CSRF token when a session starts or ends, so the cached one is dropped
  private async changeSession(endpoint: string, options: RequestInit): Promise<AuthResponse> {
    const response = await this.request(endpoint, options)
    clearCsrfToken()
    return response
  }

  private async passwordAction(endpoint: string, body: object): Promise<PasswordActionResponse> {
    const { success, error, code } = await this.request(endpoint, { method: 'POST', body: JSON.stringify(body) })
    return { success, error, code }
  }

  /** Ask for a reset link. The backend answers the same for every address, so success means "asked". */
  async requestPasswordReset(email: string): Promise<PasswordActionResponse> {
    return this.passwordAction('/api/v1/auth/password-reset/request/', { email })
  }

  async confirmPasswordReset(data: ResetPasswordRequest): Promise<PasswordActionResponse> {
    return this.passwordAction('/api/v1/auth/password-reset/confirm/', data)
  }

  /** The current session stays signed in; the account's other sessions end. */
  async changePassword(data: ChangePasswordRequest): Promise<PasswordActionResponse> {
    return this.passwordAction('/api/v1/auth/password/change/', data)
  }

  async register(data: RegisterRequest): Promise<AuthResponse> {
    return this.changeSession('/api/v1/auth/register/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async login(data: LoginRequest): Promise<AuthResponse> {
    return this.changeSession('/api/v1/auth/login/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async logout(): Promise<AuthResponse> {
    return this.changeSession('/api/v1/auth/logout/', {
      method: 'POST',
    })
  }

  async refresh(): Promise<AuthResponse> {
    return this.request('/api/v1/auth/refresh/', {
      method: 'POST',
    })
  }

  /**
   * With onlyIfSession, first ask GET /auth/csrf/ whether the session is logged in and skip
   * /auth/me/ when it is not (an anonymous visit then makes no 401 request).
   */
  async getCurrentUser(options: { onlyIfSession?: boolean } = {}): Promise<AuthResponse> {
    if (options.onlyIfSession) {
      try {
        const response = await fetch(`${this.baseUrl}/api/v1/auth/csrf/`, { credentials: 'include' })
        const data = response.ok ? await response.json() : null
        if (data?.authenticated === false) {
          return { success: false, error: 'Not logged in' }
        }
      } catch {
        // Could not tell: fall through to /auth/me/
      }
    }
    return this.request('/api/v1/auth/me/', {
      method: 'GET',
    })
  }

  async updateProfile(data: UpdateProfileRequest): Promise<AuthResponse> {
    return this.request('/api/v1/auth/me/update/', {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }
}

// Export singleton instance
export const authAdapter = new AuthAdapter()

// Export class for testing
export { AuthAdapter }
