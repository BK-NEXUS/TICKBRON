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
  // True once the number was proven by an SMS code; only then can it be used to log in
  phone_verified?: boolean
  two_factor_enabled: boolean
  is_staff?: boolean
  is_superuser?: boolean
  // Role name, e.g. 'hotel-owner'; null for regular users. Read-only on the backend
  role?: string | null
}

export interface RegisterRequest {
  email: string
  full_name: string
  phone_number: string
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

export interface RequestOTPRequest {
  phone_number: string
}

export interface VerifyOTPRequest {
  phone_number: string
  otp_code: string
}

export interface OTPResponse {
  success: boolean
  otp_code?: string
  error?: string
  /** Machine-readable reason from the backend, e.g. 'phone_already_verified' */
  code?: string
  detail?: string
}

export interface AuthResponse {
  success: boolean
  user?: User
  error?: string
  /** Machine-readable reason from the backend, e.g. 'otp_invalid' */
  code?: string
  detail?: string
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

  async requestOTP(data: RequestOTPRequest): Promise<OTPResponse> {
    const url = `${this.baseUrl}/api/v1/auth/otp/request/`
    
    try {
      const response = await apiFetch(url, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })
      
      if (!response.ok) {
        const apiError = await readApiError(response)
        return {
          success: false,
          error: apiError.message,
        }
      }

      const responseData = await response.json()
      return {
        success: true,
        otp_code: responseData.otp_code,
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error occurred',
      }
    }
  }

  async verifyOTP(data: VerifyOTPRequest): Promise<AuthResponse> {
    return this.changeSession('/api/v1/auth/otp/verify/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  /** Send a code to the logged-in user's own number; the backend takes the number from the account. */
  async requestPhoneVerification(): Promise<OTPResponse> {
    const response = await apiFetch(`${this.baseUrl}/api/v1/auth/phone/verify/request/`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: '{}',
    }).catch(() => null)
    if (!response) return { success: false, error: 'Network error occurred' }
    if (!response.ok) {
      const apiError = await readApiError(response)
      return { success: false, error: apiError.message, code: apiError.code }
    }
    const data = await response.json()
    return { success: true, otp_code: data.otp_code }
  }

  /** Prove the number with the SMS code; success returns the user with phone_verified true. */
  async confirmPhoneVerification(otpCode: string): Promise<AuthResponse> {
    return this.request('/api/v1/auth/phone/verify/confirm/', {
      method: 'POST',
      body: JSON.stringify({ otp_code: otpCode }),
    })
  }
}

// Export singleton instance
export const authAdapter = new AuthAdapter()

// Export class for testing
export { AuthAdapter }
