// Session tiykarlı autentifikaciya ushın Auth API adapteri
// 03-04 Checkpoint teği backend auth endpoint leri menen birlesedi

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
  /** Eki basqıshlı kirisiwdi sazlawı kerek hám sazlamaǵan administrator ushın True: sayt sazlaw betin kórsetedi */
  two_factor_setup_required?: boolean
  is_staff?: boolean
  is_superuser?: boolean
  // Rol atı, mısalı 'hotel-owner'; ápiwayı paydalanıwshılar ushın null. Backend te tek oqıw
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
  /** Backend ten mashina oqıytuǵın sebep, mısalı 'otp_invalid' */
  code?: string
  detail?: string
  /** Parol durıs edi, biraq ilova kodı da jiberilmegenshe hesh kim kirgizilmeydi */
  twoFactorRequired?: boolean
  /**
   * Altı sanlı kod e-mail ge jiberildi: dizimnen ótiw akkauntti tek kod terilgennen keyin jaratadı, kirisiw tek sonnan keyin
   * baslanadı
   */
  emailCodeRequired?: boolean
  /** Dizimnen ótiw: kod barǵan mánzil */
  email?: string
  /** Kirisiw: "o***@gmail.com" */
  emailHint?: string
  /** Jańa kod soraw múmkin bolǵanǵa shekem sekundlar */
  resendAfter?: number
}

/** Ilovanıń 6 sanı, yamasa zapas kodlardıń biri */
export type TwoFactorCredential = { code: string } | { backupCode: string }

export interface TwoFactorSetupResponse {
  success: boolean
  error?: string
  /** Authenticator ilovası QR koddan oqıytuǵın otpauth:// siltemesi */
  otpauthUri?: string
  /** Sol sır tekst retinde, qolda teriw ushın */
  secret?: string
}

export interface TwoFactorConfirmResponse {
  success: boolean
  error?: string
  /** Bir márte kórsetiledi: telefon joǵalǵanda jalǵız kiriw jolı */
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

/** Parol shaqırıwınıń juwabı: tek islegenin yamasa joq ekeni, hesh qashan akkaunt emes. */
export interface PasswordActionResponse {
  success: boolean
  error?: string
  /** Backend ten mashina oqıytuǵın sebep, mısalı 'invalid_reset_link' */
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
      credentials: 'include', // Cookie li session tiykarlı auth ushın áhmiyetli
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
      if (data?.email_code_required) {
        return {
          success: true, emailCodeRequired: true, email: data.email, emailHint: data.email_hint,
          resendAfter: data.resend_after,
        }
      }
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

  // Django session baslanǵanda yamasa pitkende CSRF token di aylandıradı, sol sebepli keshtegisi taslanadı
  private async changeSession(endpoint: string, options: RequestInit): Promise<AuthResponse> {
    const response = await this.request(endpoint, options)
    clearCsrfToken()
    return response
  }

  private async passwordAction(endpoint: string, body: object): Promise<PasswordActionResponse> {
    const { success, error, code } = await this.request(endpoint, { method: 'POST', body: JSON.stringify(body) })
    return { success, error, code }
  }

  /** Tiklew siltemesin soraw. Backend hár mánzil ushın birdey juwap beredi, sol sebepli tabıs "soraldı" degendi bildiredi. */
  async requestPasswordReset(email: string): Promise<PasswordActionResponse> {
    return this.passwordAction('/api/v1/auth/password-reset/request/', { email })
  }

  async confirmPasswordReset(data: ResetPasswordRequest): Promise<PasswordActionResponse> {
    return this.passwordAction('/api/v1/auth/password-reset/confirm/', data)
  }

  /** Házirgi session kirgen qaladı; akkaunttıń basqa session ları tawsıladı. */
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

  /**
   * Dizimnen ótiwdiń aqırǵı qádemi, register() emailCodeRequired dep juwap bergennen keyin: durıs kod akkauntti jaratadı hám
   * kirgizedi
   */
  async verifyRegistration(email: string, code: string): Promise<AuthResponse> {
    return this.changeSession('/api/v1/auth/register/verify/', { method: 'POST', body: JSON.stringify({ email, code }) })
  }

  /** Kútip turǵan dizimnen ótiw ushın jańa kod */
  async resendRegistrationCode(email: string): Promise<AuthResponse> {
    return this.request('/api/v1/auth/register/resend/', { method: 'POST', body: JSON.stringify({ email }) })
  }

  /** Mehmann yamasa mehmanxana iyesi kirisiwiniń ekinshi qádemi, login() emailCodeRequired dep juwap bergennen keyin */
  async loginEmailCode(code: string): Promise<AuthResponse> {
    return this.changeSession('/api/v1/auth/login/email-code/', { method: 'POST', body: JSON.stringify({ code }) })
  }

  /** Kútip turǵan kirisiw ushın jańa kod */
  async resendLoginCode(): Promise<AuthResponse> {
    return this.request('/api/v1/auth/login/email-code/resend/', { method: 'POST', body: JSON.stringify({}) })
  }

  /** Kirisiwdiń ekinshi qádemi, login() twoFactorRequired dep juwap bergennen keyin */
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

  /** Kirgen paydalanıwshınıń authenticator ilovası ushın jańa sır; confirmTwoFactorSetup ǵa shekem hesh nárse qosılmaydı */
  async startTwoFactorSetup(): Promise<TwoFactorSetupResponse> {
    const { data, error } = await this.post<{ otpauth_uri: string; secret: string }>('/api/v1/auth/2fa/setup/')
    return data ? { success: true, otpauthUri: data.otpauth_uri, secret: data.secret } : { success: false, error }
  }

  /** Birinshi durıs kod onı qosadı; zapas kodlar usı bir márte qaytadı */
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
   * onlyIfSession menen aldın GET /auth/csrf/ dan session kirgen be dep soraydı hám kirmegen bolsa
   * /auth/me/ ti ótkizip jiberedi (anonim kirgende 401 soraw bolmaydı).
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
        // Anıqlap bolmadı: /auth/me/ ge ótiw
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

// Singleton nusqasın eksport etiw
export const authAdapter = new AuthAdapter()

// Testlew ushın klasstı eksport etiw
export { AuthAdapter }
