const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Favorite types from backend contract
export interface Favorite {
  id: number
  user: number
  property: number
  property_name: string
  city: string
  country: string
  base_price: number
  currency: string
  primary_photo?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface FavoriteCount {
  count: number
}

// Account History types from backend contract
export interface AccountHistory {
  id: number
  user: number
  action: string
  description: string
  metadata?: Record<string, unknown>
  ip_address?: string
  user_agent?: string
  created_at: string
}

export interface AccountHistoryStats {
  total_entries: number
  action_counts: Record<string, number>
}

// Booking types from backend contract (reused from bookingAdapter)
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

export interface BookingItem {
  id: number
  booking: number
  room_type: number
  room_type_name: string
  rate_plan: number
  rate_plan_name: string
  check_in: string
  check_out: string
  number_of_nights: number
  price: number
  currency: string
  created_at: string
  updated_at: string
}

// API Response types
export interface ApiResponse<T> {
  data: T | null
  error: string | null
}

export const accountAdapter = {
  // Favorites API methods
  async getFavorites(): Promise<ApiResponse<Favorite[]>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/me/favorites/`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        if (response.status === 401) {
          return { data: null, error: 'Authentication required' }
        }
        const errorData = await response.json().catch(() => ({}))
        return { data: null, error: errorData.detail || 'Failed to fetch favorites' }
      }

      const data = await response.json()
      return { data, error: null }
    } catch (error) {
      return { data: null, error: 'Network error occurred' }
    }
  },

  async addFavorite(propertyId: number, notes?: string): Promise<ApiResponse<Favorite>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/me/favorites/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          property_id: propertyId,
          notes: notes || undefined,
        }),
      })

      if (!response.ok) {
        if (response.status === 401) {
          return { data: null, error: 'Authentication required' }
        }
        if (response.status === 404) {
          return { data: null, error: 'Property not found' }
        }
        const errorData = await response.json().catch(() => ({}))
        return { data: null, error: errorData.detail || 'Failed to add favorite' }
      }

      const data = await response.json()
      return { data, error: null }
    } catch (error) {
      return { data: null, error: 'Network error occurred' }
    }
  },

  async removeFavorite(favoriteId: number): Promise<ApiResponse<null>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/me/favorites/${favoriteId}/`, {
        method: 'DELETE',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        if (response.status === 401) {
          return { data: null, error: 'Authentication required' }
        }
        if (response.status === 404) {
          return { data: null, error: 'Favorite not found' }
        }
        const errorData = await response.json().catch(() => ({}))
        return { data: null, error: errorData.detail || 'Failed to remove favorite' }
      }

      return { data: null, error: null }
    } catch (error) {
      return { data: null, error: 'Network error occurred' }
    }
  },

  async getFavoriteCount(): Promise<ApiResponse<FavoriteCount>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/me/favorites/count/`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        if (response.status === 401) {
          return { data: null, error: 'Authentication required' }
        }
        const errorData = await response.json().catch(() => ({}))
        return { data: null, error: errorData.detail || 'Failed to fetch favorite count' }
      }

      const data = await response.json()
      return { data, error: null }
    } catch (error) {
      return { data: null, error: 'Network error occurred' }
    }
  },

  // Account History API methods
  async getAccountHistory(): Promise<ApiResponse<AccountHistory[]>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/me/history/`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        if (response.status === 401) {
          return { data: null, error: 'Authentication required' }
        }
        const errorData = await response.json().catch(() => ({}))
        return { data: null, error: errorData.detail || 'Failed to fetch account history' }
      }

      const data = await response.json()
      return { data, error: null }
    } catch (error) {
      return { data: null, error: 'Network error occurred' }
    }
  },

  async getRecentHistory(limit: number = 10): Promise<ApiResponse<AccountHistory[]>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/me/history/recent/?limit=${limit}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        if (response.status === 401) {
          return { data: null, error: 'Authentication required' }
        }
        if (response.status === 400) {
          return { data: null, error: 'Invalid limit parameter' }
        }
        const errorData = await response.json().catch(() => ({}))
        return { data: null, error: errorData.detail || 'Failed to fetch recent history' }
      }

      const data = await response.json()
      return { data, error: null }
    } catch (error) {
      return { data: null, error: 'Network error occurred' }
    }
  },

  async getAccountHistoryStats(): Promise<ApiResponse<AccountHistoryStats>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/me/history/stats/`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        if (response.status === 401) {
          return { data: null, error: 'Authentication required' }
        }
        const errorData = await response.json().catch(() => ({}))
        return { data: null, error: errorData.detail || 'Failed to fetch account history stats' }
      }

      const data = await response.json()
      return { data, error: null }
    } catch (error) {
      return { data: null, error: 'Network error occurred' }
    }
  },

  // Booking History API methods (using booking endpoint from checkpoint 13-14)
  async getBookings(status?: string, paymentStatus?: string): Promise<ApiResponse<Booking[]>> {
    try {
      const params = new URLSearchParams()
      if (status) params.append('status', status)
      if (paymentStatus) params.append('payment_status', paymentStatus)

      const response = await fetch(`${API_BASE_URL}/api/v1/bookings/?${params.toString()}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        if (response.status === 401) {
          return { data: null, error: 'Authentication required' }
        }
        if (response.status === 403) {
          return { data: null, error: 'Unauthorized access' }
        }
        const errorData = await response.json().catch(() => ({}))
        return { data: null, error: errorData.detail || 'Failed to fetch bookings' }
      }

      const data = await response.json()
      return { data, error: null }
    } catch (error) {
      return { data: null, error: 'Network error occurred' }
    }
  },
}
