// Property API adapter for search and property detail endpoints
// Integrates with backend property endpoints from Checkpoint 10-11

import { readApiError } from '../utils/errorHandler'
import { apiFetch } from '../utils/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface PropertyType {
  id: number
  name: string
  slug: string
}

export interface PropertyTranslation {
  language: string
  name: string
  description: string
  address_line1?: string
  address_line2?: string
}

export interface PropertyPolicy {
  policy_type: string
  title: string
  description: string
  is_strict: boolean
}

export interface AmenityCategory {
  id: number
  name: string
  slug: string
  description: string
  icon: string
  sort_order: number
}

export interface Amenity {
  id: number
  category: AmenityCategory
  name: string
  slug: string
  description: string
  icon: string
  is_searchable: boolean
  sort_order: number
}

export interface PropertyAmenity {
  amenity: Amenity
  is_available: boolean
  notes?: string
}

export interface PropertyPhoto {
  id: number
  photo: string
  photo_type: string
  caption?: string
  is_primary: boolean
  display_order: number
  alt_text?: string
}

export interface NearbyPlace {
  id: number
  name: string
  category: string
  distance: number
  distance_unit: string
  rating?: number
  address?: string
}

export interface Restaurant {
  id: number
  name: string
  cuisine: string
  distance: number
  distance_unit: string
  rating?: number
  price_range: string
  address?: string
}

export interface RoomType {
  id: number
  name: string
  slug: string
  description: string
  base_occupancy: number
  max_occupancy: number
  base_price: number
  currency: string
  total_rooms: number
  bed_configuration: string
  room_size?: number
  photos?: PropertyPhoto[]
  amenities?: PropertyAmenity[]
  rate_plans?: RatePlan[]
}

export interface RatePlan {
  id: number
  name: string
  slug: string
  rate_type: string
  description: string
  base_price: number
  currency: string
  min_nights: number
  max_nights: number
  is_active: boolean
  cancellation_policy: string
  deposit_required: boolean
  deposit_percentage?: number
  advance_booking_days?: number
}

export interface DateInventory {
  id: number
  date: string
  status: string
  available_rooms: number
  booked_rooms: number
  price: number
  currency: string
  min_stay: number
  max_stay: number
  is_available: boolean
  rate_plan_id?: number
}

// GET /api/v1/properties/{id}/availability/ (backend PropertyAvailabilitySerializer).
// Decimal fields arrive as strings; price is null when the rate plan's base price applies.
export interface AvailabilityDateInventory {
  id: number
  date: string
  available_rooms: number
  booked_rooms: number
  remaining_rooms: number
  price: string | null
  currency: string
  is_available: boolean
  minimum_stay: number | null
  maximum_stay: number | null
  notes: string | null
}

export interface AvailabilityRatePlan {
  id: number
  date_inventory: AvailabilityDateInventory[]
}

export interface AvailabilityRoomType {
  id: number
  rate_plans: AvailabilityRatePlan[]
}

export interface PropertyAvailabilityResponse {
  id: number
  room_types: AvailabilityRoomType[]
}

export interface QuoteParams {
  roomTypeId: number
  ratePlanId: number
  checkIn: string
  /** Exclusive: the day the guest leaves */
  checkOut: string
  rooms: number
}

// GET /api/v1/properties/{id}/quote/: the same pricing Booking.create_booking charges
export interface StayQuote {
  check_in: string
  check_out: string
  number_of_nights: number
  number_of_rooms: number
  currency: string
  nights: Array<{ date: string; price: string }>
  total_price: string
  /** The same stay in so'm at today's rate; null when no rate is stored yet */
  uzs_total?: string | null
  exchange_rate?: { rate: string; date: string | null; source: string; stale: boolean } | null
  /** R12b: what the guest is told about the no-show refund */
  no_show_refund_percent?: number
  no_show_refund_amount?: string | null
  no_show_refund_text_key?: string | null
  no_show_refund_text_params?: { percent: number; amount: string | null } | null
}

export interface AvailabilityParams {
  check_in: string
  check_out: string
}

export interface Property {
  id: number
  owner_id: number
  property_type: PropertyType
  status: string
  max_guests: number
  bedrooms: number
  bathrooms: number
  address_line1: string
  address_line2?: string
  city: string
  state?: string
  postal_code?: string
  country: string
  latitude?: number
  longitude?: number
  base_price: number
  currency: string
  total_area?: number
  floor_number?: number
  has_elevator: boolean
  has_parking: boolean
  has_wifi: boolean
  has_ac: boolean
  has_heating: boolean
  name?: string
  description?: string
  translations: PropertyTranslation[]
  policies: PropertyPolicy[]
  amenities?: PropertyAmenity[]
  room_types?: RoomType[]
  gallery?: Record<string, PropertyPhoto[]>
  rating?: number
  /** Search results: average of approved reviews (null when there are none) */
  average_rating?: number | null
  review_count?: number
  primary_photo?: PropertyPhoto
  nearby_places?: NearbyPlace[]
  restaurants?: Restaurant[]
  created_at: string
  updated_at: string
}

export interface SearchParams {
  q?: string
  location?: string
  lat?: number
  lng?: number
  radius?: number
  min_price?: number
  max_price?: number
  min_guests?: number
  max_guests?: number
  amenities?: number[]
  property_type?: number
  /** Property flags that must all be set: wifi, parking, ac, heating, elevator */
  features?: string[]
  /** Minimum average guest rating, 1-5 */
  min_rating?: number
  check_in?: string
  check_out?: string
  sort?: string
  page?: number
  page_size?: number
}

export interface FilterOptions {
  property_types: Array<PropertyType & { count: number }>
  features: Array<{ id: string; label: string; count: number }>
  amenities: Array<{ id: number; name: string; slug: string; icon?: string | null; count: number }>
  price_range: { min: number | null; max: number | null }
  sort_options: Array<{ id: string; label: string }>
}

export interface SearchResponse {
  count: number
  next: string | null
  previous: string | null
  results: Property[]
  page: number
  page_size: number
  total_pages: number
  /** Paid banners for the top of page 1 (R10); absent on older backends and on other pages */
  promoted?: Array<Property & { promotion_id: number }>
}

export interface PropertyDetailResponse extends Property {
  gallery: Record<string, PropertyPhoto[]>
  room_types: RoomType[]
  amenities: PropertyAmenity[]
  nearby_places?: NearbyPlace[]
  restaurants?: Restaurant[]
}

export interface ApiError {
  error: string
  details?: string | Record<string, string[]>
}

class PropertyAdapter {
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
      const response = await apiFetch(url, defaultOptions)
      
      if (!response.ok) {
        const apiError = await readApiError(response)
        return { data: null, error: apiError.message }
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
   * Search properties based on search parameters
   * Integrates with GET /api/v1/properties/search/ endpoint
   */
  async searchProperties(params: SearchParams): Promise<{ data: SearchResponse | null; error: string | null }> {
    const queryParams = new URLSearchParams()
    
    if (params.q) queryParams.append('q', params.q)
    if (params.location) queryParams.append('location', params.location)
    if (params.lat !== undefined) queryParams.append('lat', params.lat.toString())
    if (params.lng !== undefined) queryParams.append('lng', params.lng.toString())
    if (params.radius !== undefined) queryParams.append('radius', params.radius.toString())
    if (params.min_price !== undefined) queryParams.append('min_price', params.min_price.toString())
    if (params.max_price !== undefined) queryParams.append('max_price', params.max_price.toString())
    if (params.min_guests !== undefined) queryParams.append('min_guests', params.min_guests.toString())
    if (params.max_guests !== undefined) queryParams.append('max_guests', params.max_guests.toString())
    if (params.amenities && params.amenities.length > 0) {
      queryParams.append('amenities', params.amenities.join(','))
    }
    if (params.property_type !== undefined) queryParams.append('property_type', params.property_type.toString())
    if (params.features && params.features.length > 0) queryParams.append('features', params.features.join(','))
    if (params.min_rating !== undefined) queryParams.append('min_rating', params.min_rating.toString())
    if (params.check_in) queryParams.append('check_in', params.check_in)
    if (params.check_out) queryParams.append('check_out', params.check_out)
    if (params.sort) queryParams.append('sort', params.sort)
    if (params.page !== undefined) queryParams.append('page', params.page.toString())
    if (params.page_size !== undefined) queryParams.append('page_size', params.page_size.toString())

    const queryString = queryParams.toString()
    const endpoint = `/api/v1/properties/search/${queryString ? `?${queryString}` : ''}`
    
    return this.request<SearchResponse>(endpoint)
  }

  /**
   * What the search sidebar can filter and sort by
   * Integrates with GET /api/v1/properties/filter-options/ endpoint
   */
  async getFilterOptions(): Promise<{ data: FilterOptions | null; error: string | null }> {
    return this.request<FilterOptions>('/api/v1/properties/filter-options/')
  }

  /**
   * Get search suggestions for autocomplete
   * Integrates with GET /api/v1/properties/search/suggestions/ endpoint
   */
  async getSearchSuggestions(query: string, limit: number = 5): Promise<{ data: { suggestions: string[] } | null; error: string | null }> {
    const queryParams = new URLSearchParams()
    queryParams.append('q', query)
    queryParams.append('limit', limit.toString())
    
    const endpoint = `/api/v1/properties/search/suggestions/?${queryParams.toString()}`
    
    return this.request<{ suggestions: string[] }>(endpoint)
  }

  /**
   * Get property details by ID
   * Integrates with GET /api/v1/properties/{id}/ endpoint
   */
  async getPropertyById(id: number): Promise<{ data: PropertyDetailResponse | null; error: string | null }> {
    return this.request<PropertyDetailResponse>(`/api/v1/properties/${id}/`)
  }

  /**
   * Get per-date availability and prices for a property
   * Integrates with GET /api/v1/properties/{id}/availability/?check_in=&check_out= (dates inclusive)
   */
  async getAvailability(
    propertyId: number,
    params: AvailabilityParams
  ): Promise<{ data: PropertyAvailabilityResponse | null; error: string | null }> {
    const query = new URLSearchParams({ check_in: params.check_in, check_out: params.check_out })
    return this.request<PropertyAvailabilityResponse>(`/api/v1/properties/${propertyId}/availability/?${query.toString()}`)
  }

  /**
   * Price a stay with the code that charges for it.
   * GET /api/v1/properties/{id}/quote/ (check_out exclusive). On 400 the error is the
   * backend's reason, e.g. "2026-09-28 is not available."
   */
  async getQuote(
    propertyId: number,
    params: QuoteParams
  ): Promise<{ data: StayQuote | null; error: string | null }> {
    const query = new URLSearchParams({
      room_type_id: String(params.roomTypeId),
      rate_plan_id: String(params.ratePlanId),
      check_in: params.checkIn,
      check_out: params.checkOut,
      rooms: String(params.rooms),
    })
    try {
      const response = await apiFetch(`${this.baseUrl}/api/v1/properties/${propertyId}/quote/?${query.toString()}`, {
        credentials: 'include',
      })
      if (!response.ok) {
        const apiError = await readApiError(response)
        // The field message ("... is not available.") is clearer than the envelope text
        const reason = apiError.fieldErrors ? Object.values(apiError.fieldErrors).flat()[0] : undefined
        return { data: null, error: reason || apiError.message }
      }
      return { data: await response.json(), error: null }
    } catch (error) {
      return { data: null, error: error instanceof Error ? error.message : 'Network error occurred' }
    }
  }
}

// Export singleton instance
export const propertyAdapter = new PropertyAdapter()

// Export class for testing
export { PropertyAdapter }
