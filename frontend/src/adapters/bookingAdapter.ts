// Bron endpoint leri ushın Booking API adapteri
// 13-14 Checkpoint degi backend bron endpoint leri menen birlesedi

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

/** Bron alınǵan CBU kursı (mehmanxana valyutasınıń bir birligine UZS) */
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
  /** Mehmannan alınatuǵın summa, R6 dan beri jasalǵan bronlar ushın UZS de; eski bronlarda joq (alınatuǵın = baha) */
  charge_amount?: string
  charge_currency?: string
  exchange_rate?: ExchangeRateInfo | null
  /** Mehmanxanada naqd: mehmannıń keletuǵının aytqan waqtı ('10:30:00'); eski bronlarda joq */
  expected_arrival_time?: string | null
  /** Mehmanxana mehmandı kelgen dep belgilegen waqıt */
  arrived_at?: string | null
  /** Usı waqıttan keyin kelmegen mehmannıń broni biykar etiledi */
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
  /** Kiriw kúni 'HH:MM' (mehmanxanada naqd) */
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
   * Jańa bron jaratıw
   * POST /api/v1/bookings/ endpoint i menen birlesedi
   */
  /** `code` backend tiń qátelik mashina kodı (mısalı `exchange_rate_unavailable`) */
  async createBooking(
    request: BookingCreateRequest,
  ): Promise<{ data: Booking | null; error: string | null; code?: string; reason?: Refusal }> {
    return this.request<Booking>('/api/v1/bookings/', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  /**
   * Házirgi paydalanıwshınıń bronların alıw
   * GET /api/v1/bookings/ endpoint i menen birlesedi
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
   * Belgili bir bronnı ID boyınsha alıw
   * GET /api/v1/bookings/{id}/ endpoint i menen birlesedi
   */
  async getBookingById(id: number): Promise<{ data: Booking | null; error: string | null }> {
    return this.request<Booking>(`/api/v1/bookings/${id}/`)
  }

  /**
   * Bronnan bas tartıw
   * POST /api/v1/bookings/{id}/cancel/ endpoint i menen birlesedi
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

// Singleton nusqasın eksport etiw
export const bookingAdapter = new BookingAdapter()

// Testlew ushın klasstı eksport etiw
export { BookingAdapter }
