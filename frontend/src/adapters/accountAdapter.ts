import type { ExchangeRateInfo } from './bookingAdapter'
import type { PriceList } from './propertyAdapter'
import { readApiError } from '../utils/errorHandler'
import { apiFetch, fetchAllPages } from '../utils/api'
import { translateNow } from '../i18n/translateNow'
import { API_BASE_URL } from '../utils/apiBase'

// Backend contract tan Favorite túrleri
// GET /api/v1/me/favorites/ elementi (backend FavoriteSerializer). Decimal lar qatar retinde keledi.
export interface Favorite {
  id: number
  user: number
  property: number
  property_translations: Array<{ language: string; name: string; description?: string; city?: string | null }>
  property_city: string
  property_country: string
  property_base_price: string
  property_currency: string
  /** R16: mehmanxananıń hár valyutadaǵı "dan" bahası (mehmanxana kartası sıyaqlı); eski juwaplarda joq */
  property_prices?: PriceList
  property_primary_photo: string | null
  notes: string | null
  created_at: string
}

export interface FavoriteCount {
  count: number
}

// Backend contract tan Account History túrleri
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

// Backend contract tan Booking túrleri (bookingAdapter ten qayta paydalanılǵan)
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
  /** Mehmannan alınatuǵın summa, R6 dan beri jasalǵan bronlar ushın UZS de; eski bronlarda joq (alınatuǵın = baha) */
  charge_amount?: string
  charge_currency?: string
  exchange_rate?: ExchangeRateInfo | null
  /** Mehmanxanada naqd: mehmannıń keletuǵının aytqan waqtı ('10:30:00'); eski bronlarda null */
  expected_arrival_time?: string | null
  /** Mehmanxana mehmandı kelgen dep belgilegen waqıt */
  arrived_at?: string | null
}

// Backend contract tan Review túrleri
export interface Review {
  id: number
  user: number
  property: number
  booking?: number
  overall_rating: number
  cleanliness_rating?: number
  location_rating?: number
  value_rating?: number
  amenities_rating?: number
  service_rating?: number
  title?: string
  comment?: string
  status: 'pending' | 'approved' | 'rejected'
  reviewed_at?: string
  created_at: string
  updated_at: string
  owner_reply?: string
  replied_at?: string | null
}

/**
 * Hár kelwshi kóretuǵın tastıyıqlanǵan sharh (GET /api/v1/me/reviews/public/): sharh jazıwshı "Aziz K.", hesh qashan mánzil
 * emes
 */
export interface PublicReview {
  id: number
  reviewer: string
  /** Turıw ayı, YYYY-MM, yamasa bron joq bolsa null */
  stay_month?: string | null
  overall_rating: number
  cleanliness_rating?: number | null
  location_rating?: number | null
  value_rating?: number | null
  amenities_rating?: number | null
  service_rating?: number | null
  title?: string
  comment?: string
  created_at: string
  /** Mehmanxana iyesiniń ashıq juwabı (bos: ele joq) */
  owner_reply?: string
  replied_at?: string | null
}

export interface PublicReviewsPage {
  count: number
  hasMore: boolean
  results: PublicReview[]
}

// Backend ReviewCreateSerializer di kórsetedi: tegis kategoriya bahaları, `property` hám `booking` id leri.
// Bron paydalanıwshınıń óz juwmaqlanǵan, ele sharh jazılmaǵan sol mehmanxanadaǵı turıwı bolıwı kerek.
export interface CreateReviewRequest {
  property: number
  booking: number
  overall_rating: number
  cleanliness_rating?: number
  location_rating?: number
  value_rating?: number
  amenities_rating?: number
  service_rating?: number
  title?: string
  comment?: string
}

export interface EligibleProperty {
  property_id: number
  property_city: string
  property_country: string
  booking_id: number
  confirmation_code: string
  check_in: string
  check_out: string
}

export interface EligiblePropertiesResponse {
  eligible_properties: EligibleProperty[]
}

export interface PropertyScores {
  property_id: number
  total_reviews: number
  average_rating: number | null
  category_scores: {
    cleanliness_rating?: number
    location_rating?: number
    value_rating?: number
    amenities_rating?: number
    service_rating?: number
  }
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

// API Response túrleri
/** GET /api/v1/bookings/: mehmannıń óz bronlarınıń bir beti, eń jańası birinshi, bir betke 20 */
export interface BookingPage {
  count: number
  next: string | null
  previous: string | null
  results: Booking[]
}

export interface ApiResponse<T> {
  data: T | null
  error: string | null
}

const ACCOUNT_LIST_OPTIONS = {
  errorMessages: { 401: translateNow('apiError.authRequired') },
  networkErrorMessage: translateNow('apiError.networkOccurred'),
}

export const accountAdapter = {
  // Favorit API metodları
  // Backend te betlerge bólingen: hár bettiń elementlerin qaytaradı
  async getFavorites(): Promise<ApiResponse<Favorite[]>> {
    const { data, error } = await fetchAllPages<Favorite>(`${API_BASE_URL}/api/v1/me/favorites/`, ACCOUNT_LIST_OPTIONS)
    return { data, error }
  },

  async addFavorite(propertyId: number, notes?: string): Promise<ApiResponse<Favorite>> {
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/v1/me/favorites/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          property: propertyId,
          notes: notes || undefined,
        }),
      })

      if (!response.ok) {
        const apiError = await readApiError(response, { 401: translateNow('apiError.authRequired'), 404: 'Property not found' })
        return { data: null, error: apiError.message }
      }

      const data = await response.json()
      return { data, error: null }
    } catch {
      return { data: null, error: translateNow('apiError.networkOccurred') }
    }
  },

  async removeFavorite(favoriteId: number): Promise<ApiResponse<null>> {
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/v1/me/favorites/${favoriteId}/`, {
        method: 'DELETE',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const apiError = await readApiError(response, { 401: translateNow('apiError.authRequired'), 404: 'Favorite not found' })
        return { data: null, error: apiError.message }
      }

      return { data: null, error: null }
    } catch {
      return { data: null, error: translateNow('apiError.networkOccurred') }
    }
  },

  async getFavoriteCount(): Promise<ApiResponse<FavoriteCount>> {
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/v1/me/favorites/count/`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const apiError = await readApiError(response, { 401: translateNow('apiError.authRequired') })
        return { data: null, error: apiError.message }
      }

      const data = await response.json()
      return { data, error: null }
    } catch {
      return { data: null, error: translateNow('apiError.networkOccurred') }
    }
  },

  // Akkaunt tariyxı API metodları
  // Backend te betlerge bólingen: hár bettiń elementlerin qaytaradı
  async getAccountHistory(): Promise<ApiResponse<AccountHistory[]>> {
    const { data, error } = await fetchAllPages<AccountHistory>(`${API_BASE_URL}/api/v1/me/history/`, ACCOUNT_LIST_OPTIONS)
    return { data, error }
  },

  async getRecentHistory(limit: number = 10): Promise<ApiResponse<AccountHistory[]>> {
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/v1/me/history/recent/?limit=${limit}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const apiError = await readApiError(response, { 400: 'Invalid limit parameter', 401: translateNow('apiError.authRequired') })
        return { data: null, error: apiError.message }
      }

      const data = await response.json()
      return { data, error: null }
    } catch {
      return { data: null, error: translateNow('apiError.networkOccurred') }
    }
  },

  async getAccountHistoryStats(): Promise<ApiResponse<AccountHistoryStats>> {
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/v1/me/history/stats/`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const apiError = await readApiError(response, { 401: translateNow('apiError.authRequired') })
        return { data: null, error: apiError.message }
      }

      const data = await response.json()
      return { data, error: null }
    } catch {
      return { data: null, error: translateNow('apiError.networkOccurred') }
    }
  },

  // Bron tariyxı API metodları (13-14 checkpoint tan bron endpoint i paydalanıladı)
  async getBookings(status?: string, paymentStatus?: string, page = 1): Promise<ApiResponse<BookingPage>> {
    try {
      const params = new URLSearchParams()
      if (status) params.append('status', status)
      if (paymentStatus) params.append('payment_status', paymentStatus)
      if (page > 1) params.append('page', String(page))

      const response = await apiFetch(`${API_BASE_URL}/api/v1/bookings/?${params.toString()}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const apiError = await readApiError(response, { 401: translateNow('apiError.authRequired'), 403: 'Unauthorized access' })
        return { data: null, error: apiError.message }
      }

      const data = await response.json()
      return { data, error: null }
    } catch {
      return { data: null, error: translateNow('apiError.networkOccurred') }
    }
  },

  // Sharhlar API metodları
  // Backend te betlerge bólingen: hár bettiń elementlerin qaytaradı
  async getReviews(): Promise<ApiResponse<Review[]>> {
    const { data, error } = await fetchAllPages<Review>(`${API_BASE_URL}/api/v1/me/reviews/`, ACCOUNT_LIST_OPTIONS)
    return { data, error }
  },

  async createReview(reviewData: CreateReviewRequest): Promise<ApiResponse<Review>> {
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/v1/me/reviews/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(reviewData),
      })

      if (!response.ok) {
        const apiError = await readApiError(response, { 400: 'Invalid review data', 401: translateNow('apiError.authRequired'), 404: 'Property or booking not found' })
        return { data: null, error: apiError.message }
      }

      const data = await response.json()
      return { data, error: null }
    } catch {
      return { data: null, error: translateNow('apiError.networkOccurred') }
    }
  },

  async getEligibleProperties(): Promise<ApiResponse<EligiblePropertiesResponse>> {
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/v1/me/reviews/eligible_properties/`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const apiError = await readApiError(response, { 401: translateNow('apiError.authRequired') })
        return { data: null, error: apiError.message }
      }

      const data = await response.json()
      return { data, error: null }
    } catch {
      return { data: null, error: translateNow('apiError.networkOccurred') }
    }
  },

  /** Mehmanxananıń tastıyıqlanǵan sharhlarınıń bir beti (20), eń jańası birinshi; ashıq, kirisiw kerek emes */
  async getPublicReviews(propertyId: number, page = 1): Promise<ApiResponse<PublicReviewsPage>> {
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/v1/me/reviews/public/?property_id=${propertyId}&page=${page}`, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      })

      if (!response.ok) {
        const apiError = await readApiError(response, {})
        return { data: null, error: apiError.message }
      }

      const body = await response.json()
      return { data: { count: body.count, hasMore: Boolean(body.next), results: body.results }, error: null }
    } catch {
      return { data: null, error: translateNow('apiError.networkOccurred') }
    }
  },

  async getPropertyScores(propertyId: number): Promise<ApiResponse<PropertyScores>> {
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/v1/me/reviews/property_scores/?property_id=${propertyId}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const apiError = await readApiError(response, { 401: translateNow('apiError.authRequired') })
        return { data: null, error: apiError.message }
      }

      const data = await response.json()
      return { data, error: null }
    } catch {
      return { data: null, error: translateNow('apiError.networkOccurred') }
    }
  },
}
