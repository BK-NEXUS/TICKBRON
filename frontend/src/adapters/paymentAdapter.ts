// Payment API adapter for payment endpoints
// Integrates with backend payment endpoints from Checkpoint 15-16

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export type PaymentStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'refunded' | 'partially_refunded'
export type PaymentProvider = 'payme' | 'click' | 'visa'

export interface PaymentTransaction {
  id: number
  idempotency_key: string
  booking: number
  provider: PaymentProvider
  provider_transaction_id: string | null
  amount: number
  currency: string
  status: PaymentStatus
  payment_method_token: string | null
  provider_response: Record<string, unknown> | null
  error_code: string | null
  error_message: string | null
  client_ip: string | null
  user_agent: string | null
  created_at: string
  updated_at: string
}

export interface PaymentCreateRequest {
  idempotency_key: string
  booking: number
  provider: PaymentProvider
  amount: number
  currency: string
  payment_method_token?: string
  client_ip?: string
  user_agent?: string
}

export interface PaymentConfirmRequest {
  // No additional fields required for confirmation
}

export interface PaymentRefundRequest {
  amount?: number
}

export interface ApiError {
  error: string
  details?: string | Record<string, string[]>
}

class PaymentAdapter {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<{ data: T | null; error: string | null }> {
    const url = `${this.baseUrl}${endpoint}`
    
    const defaultOptions: RequestInit = {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    }

    try {
      const response = await fetch(url, defaultOptions)
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = 
          errorData.detail || 
          errorData.error || 
          `HTTP ${response.status}: ${response.statusText}`
        return { data: null, error: errorMessage }
      }

      const data = await response.json()
      return { data, error: null }
    } catch (error) {
      return {
        data: null,
        error: error instanceof Error ? error.message : 'Network error occurred',
      }
    }
  }

  /**
   * Create a new payment transaction
   * Integrates with POST /api/v1/payments/transactions/ endpoint
   * 
   * @param request - Payment creation request with idempotency key
   * @returns Payment transaction or error
   */
  async createPayment(request: PaymentCreateRequest): Promise<{ data: PaymentTransaction | null; error: string | null }> {
    return this.request<PaymentTransaction>('/api/v1/payments/transactions/', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  /**
   * Confirm a payment transaction
   * Integrates with POST /api/v1/payments/transactions/{id}/confirm/ endpoint
   * 
   * @param id - Payment transaction ID
   * @returns Updated payment transaction or error
   */
  async confirmPayment(id: number): Promise<{ data: PaymentTransaction | null; error: string | null }> {
    return this.request<PaymentTransaction>(`/api/v1/payments/transactions/${id}/confirm/`, {
      method: 'POST',
      body: JSON.stringify({}),
    })
  }

  /**
   * Refund a payment transaction
   * Integrates with POST /api/v1/payments/transactions/{id}/refund/ endpoint
   * 
   * @param id - Payment transaction ID
   * @param request - Optional refund amount
   * @returns Updated payment transaction or error
   */
  async refundPayment(id: number, request?: PaymentRefundRequest): Promise<{ data: PaymentTransaction | null; error: string | null }> {
    return this.request<PaymentTransaction>(`/api/v1/payments/transactions/${id}/refund/`, {
      method: 'POST',
      body: JSON.stringify(request || {}),
    })
  }

  /**
   * Get a specific payment transaction by ID
   * Integrates with GET /api/v1/payments/transactions/{id}/ endpoint
   * 
   * @param id - Payment transaction ID
   * @returns Payment transaction or error
   */
  async getPaymentById(id: number): Promise<{ data: PaymentTransaction | null; error: string | null }> {
    return this.request<PaymentTransaction>(`/api/v1/payments/transactions/${id}/`)
  }

  /**
   * Generate a unique idempotency key for payment requests
   * Prevents duplicate payment charges
   * 
   * @returns Unique idempotency key
   */
  generateIdempotencyKey(): string {
    return `payment_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`
  }

  /**
   * Get client IP address for audit trail
   * Note: This is a simplified version - actual IP may need to come from backend
   * 
   * @returns Client IP address or null
   */
  async getClientIp(): Promise<string | null> {
    try {
      const response = await fetch('https://api.ipify.org?format=json')
      const data = await response.json()
      return data.ip || null
    } catch {
      return null
    }
  }

  /**
   * Get user agent string for audit trail
   * 
   * @returns User agent string
   */
  getUserAgent(): string {
    return navigator.userAgent
  }
}

// Export singleton instance
export const paymentAdapter = new PaymentAdapter()

// Export class for testing
export { PaymentAdapter }
