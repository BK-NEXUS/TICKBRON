// Booking API adapter for booking endpoints
// Integrates with backend booking endpoints from Checkpoint 13-14

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

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

export interface Booking {
  id: number
  guest: number
  guest_name: string
  property: number
  property_name: string
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed' | 'no_show'
  payment_status: 'pending' | 'paid' | 'failed' | 'refunded' | 'partially_refunded'
  check_in: string
  check_out: string
  number_of_nights: number
  guest_count: number
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
}

export interface BookingCreateRequest {
  property_id: number
  room_type_id: number
  rate_plan_id: number
  check_in: string
  check_out: string
  guest_count: number
  special_requests?: string
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
   * Create a new booking
   * Integrates with POST /api/v1/bookings/ endpoint
   */
  async createBooking(request: BookingCreateRequest): Promise<{ data: Booking | null; error: string | null }> {
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
  async cancelBooking(id: number, request?: BookingCancelRequest): Promise<{ data: Booking | null; error: string | null }> {
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
