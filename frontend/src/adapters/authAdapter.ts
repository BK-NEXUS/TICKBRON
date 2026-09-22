// Auth API adapter for session-based authentication
// Integrates with backend auth endpoints from Checkpoint 03-04

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
  detail?: string
}

export interface AuthResponse {
  success: boolean
  user?: User
  error?: string
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
      const response = await fetch(url, defaultOptions)
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        return {
          success: false,
          error: errorData.detail || errorData.error || `HTTP ${response.status}: ${response.statusText}`,
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

  async register(data: RegisterRequest): Promise<AuthResponse> {
    return this.request('/api/v1/auth/register/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async login(data: LoginRequest): Promise<AuthResponse> {
    return this.request('/api/v1/auth/login/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async logout(): Promise<AuthResponse> {
    return this.request('/api/v1/auth/logout/', {
      method: 'POST',
    })
  }

  async refresh(): Promise<AuthResponse> {
    return this.request('/api/v1/auth/refresh/', {
      method: 'POST',
    })
  }

  async getCurrentUser(): Promise<AuthResponse> {
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
      const response = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        return {
          success: false,
          error: errorData.detail || errorData.error || `HTTP ${response.status}: ${response.statusText}`,
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
    return this.request('/api/v1/auth/otp/verify/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }
}

// Export singleton instance
export const authAdapter = new AuthAdapter()

// Export class for testing
export { AuthAdapter }

// Export new types
export type { RequestOTPRequest, VerifyOTPRequest, OTPResponse }
