// Booking API adapter for booking endpoints
// Integrates with backend booking endpoints from Checkpoint 13-14

import { parseApiError } from '../utils/errorHandler'
import { refusalOf, type Refusal } from '../utils/refusal'
import { apiFetch } from '../utils/api'
import { translateNow } from '../i18n/translateNow'
import { API_BASE_URL } from '../utils/apiBase'

export interface BookingItem {
  id: number
  room_type: number
  room_type_name: string
  rate_plan: number
  rate_plan_name: string
  number_of_rooms: number
  price_per_night: number
  currency: string
}

/** The CBU rate a booking was charged at (UZS per one unit of the hotel currency) */
export interface ExchangeRateInfo {
  rate: string
  date: string | null
  source: string
  stale: boolean
}

export interface Booking {
  id: number
  guest: number
  guest_name: string
  guest_full_name?: string
  guest_phone?: string
  guest_email?: string
  property: number
  property_name: string
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed' | 'no_show'
  payment_status: 'pending' | 'paid' | 'failed' | 'refunded' | 'partially_refunded'
  check_in: string
  check_out: string
  number_of_nights: number
  guest_count: number
  number_of_rooms: number
  children: number[]
  total_price: number
  currency: string
  special_requests?: string
  confirmation_code: string
  cancelled_at?: string
  cancellation_reason?: string
  expires_at?: string
  booking_items: BookingItem[]
  created_at: string
  updated_at: string
  /** What the guest is charged, in UZS for bookings made since R6; absent on older bookings (charge = price) */
  charge_amount?: string
  charge_currency?: string
  exchange_rate?: ExchangeRateInfo | null
  /** Cash at the hotel: the time the guest said they will arrive ('10:30:00'); absent on old bookings */
  expected_arrival_time?: string | null
  /** When the hotel marked the guest as arrived */
  arrived_at?: string | null
  /** After this moment a guest who has not arrived is cancelled */
  arrival_deadline?: string | null
}

export interface BookingCreateRequest {
  property_id: number
  room_type_id: number
  rate_plan_id: number
  check_in: string
  check_out: string
  guest_count: number
  guest_full_name?: string
  guest_phone?: string
  guest_email?: string
  number_of_rooms?: number
  children?: number[]
  special_requests?: string
  /** 'HH:MM' on the check-in day (cash at the hotel) */
  expected_arrival_time: string
}

export interface BookingCancelRequest {
  cancellation_reason?: string
}

export interface BookingListParams {
  status?: string
  payment_status?: string
}

export interface BookingListResponse {
  count: number
  next: string | null
  previous: string | null
  results: Booking[]
}

export interface ApiError {
  error: string
  details?: string | Record<string, string[]>
}

class BookingAdapter {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<{ data: T | null; error: string | null; code?: string; reason?: Refusal }> {
    const url = `${this.baseUrl}${endpoint}`
    
    const defaultOptions: RequestInit = {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    }

    try {
      const response = await apiFetch(url, defaultOptions)
      
      if (!response.ok) {
        const body: unknown = await response.json().catch(() => undefined)
        const apiError = parseApiError(response, body)
        return { data: null, error: apiError.message, code: apiError.code, reason: refusalOf(body) }
      }

      const data = await response.json()
      return { data, error: null }
    } catch (error) {
      return {
        data: null,
        error: error instanceof Error ? error.message : translateNow('apiError.networkOccurred'),
      }
    }
  }

  /**
   * Create a new booking
   * Integrates with POST /api/v1/bookings/ endpoint
   */
  /** `code` is the backend's machine code of a failure (for example `exchange_rate_unavailable`) */
  async createBooking(
    request: BookingCreateRequest,
  ): Promise<{ data: Booking | null; error: string | null; code?: string; reason?: Refusal }> {
    return this.request<Booking>('/api/v1/bookings/', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  /**
   * Get bookings for the current user
   * Integrates with GET /api/v1/bookings/ endpoint
   */
  async getBookings(params?: BookingListParams): Promise<{ data: BookingListResponse | null; error: string | null }> {
    const queryParams = new URLSearchParams()
    
    if (params?.status) queryParams.append('status', params.status)
    if (params?.payment_status) queryParams.append('payment_status', params.payment_status)

    const queryString = queryParams.toString()
    const endpoint = `/api/v1/bookings/${queryString ? `?${queryString}` : ''}`
    
    return this.request<BookingListResponse>(endpoint)
  }

  /**
   * Get a specific booking by ID
   * Integrates with GET /api/v1/bookings/{id}/ endpoint
   */
  async getBookingById(id: number): Promise<{ data: Booking | null; error: string | null }> {
    return this.request<Booking>(`/api/v1/bookings/${id}/`)
  }

  /**
   * Cancel a booking
   * Integrates with POST /api/v1/bookings/{id}/cancel/ endpoint
   */
  async cancelBooking(
    id: number, request?: BookingCancelRequest,
  ): Promise<{ data: Booking | null; error: string | null }> {
    return this.request<Booking>(`/api/v1/bookings/${id}/cancel/`, {
      method: 'POST',
      body: JSON.stringify(request || {}),
    })
  }
}

// Export singleton instance
export const bookingAdapter = new BookingAdapter()

// Export class for testing
export { BookingAdapter }
