// Auth API adapter for session-based authentication
// Integrates with backend auth endpoints from Checkpoint 03-04

import { readApiError } from '../utils/errorHandler'
import { apiFetch, clearCsrfToken } from '../utils/api'
import { translateNow } from '../i18n/translateNow'
import { API_BASE_URL } from '../utils/apiBase'

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
  /** True for an administrator who must set up two-step sign-in and has not: the site shows the setup page */
  two_factor_setup_required?: boolean
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

export interface AuthResponse {
  success: boolean
  user?: User
  error?: string
  /** Machine-readable reason from the backend, e.g. 'otp_invalid' */
  code?: string
  detail?: string
  /** The password was right but nobody is signed in until the app's code is sent too */
  twoFactorRequired?: boolean
}

/** The app's 6 digits, or one of the backup codes */
export type TwoFactorCredential = { code: string } | { backupCode: string }

export interface TwoFactorSetupResponse {
  success: boolean
  error?: string
  /** otpauth:// link the authenticator app reads from the QR code */
  otpauthUri?: string
  /** The same secret as text, for typing it in */
  secret?: string
}

export interface TwoFactorConfirmResponse {
  success: boolean
  error?: string
  /** Shown once: the only way in when the phone is lost */
  backupCodes?: string[]
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
      if (data?.two_factor_required) return { success: true, twoFactorRequired: true }
      return {
        success: true,
        user: data,
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : translateNow('apiError.networkOccurred'),
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

  /** Second step of the login, after login() answered twoFactorRequired */
  async loginTwoFactor(credential: TwoFactorCredential): Promise<AuthResponse> {
    const body = 'code' in credential ? { code: credential.code } : { backup_code: credential.backupCode }
    return this.changeSession('/api/v1/auth/login/2fa/', { method: 'POST', body: JSON.stringify(body) })
  }

  private async post<T>(endpoint: string, body?: object): Promise<{ data: T | null; error?: string }> {
    try {
      const response = await apiFetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      })
      if (!response.ok) return { data: null, error: (await readApiError(response)).message }
      return { data: await response.json() }
    } catch (error) {
      return { data: null, error: error instanceof Error ? error.message : translateNow('apiError.networkOccurred') }
    }
  }

  /** A new secret for the signed-in user's authenticator app; nothing is switched on until confirmTwoFactorSetup */
  async startTwoFactorSetup(): Promise<TwoFactorSetupResponse> {
    const { data, error } = await this.post<{ otpauth_uri: string; secret: string }>('/api/v1/auth/2fa/setup/')
    return data ? { success: true, otpauthUri: data.otpauth_uri, secret: data.secret } : { success: false, error }
  }

  /** The first right code switches it on; the backup codes come back this once */
  async confirmTwoFactorSetup(code: string): Promise<TwoFactorConfirmResponse> {
    const { data, error } = await this.post<{ backup_codes: string[] }>('/api/v1/auth/2fa/confirm/', { code })
    return data ? { success: true, backupCodes: data.backup_codes } : { success: false, error }
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
